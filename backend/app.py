"""
待办清单后端服务 - Flask

功能:
- 用户认证 (登录/注册)
- 任务管理 (CRUD)
- 日历功能
- MQTT 实时同步

运行: python app.py
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import json
import threading
import time

# 日期解析辅助函数
def parse_datetime(date_str):
    """解析 ISO 格式日期字符串，支持带 Z 后缀的格式"""
    if not date_str:
        return None
    # 替换 Z 为 +00:00，或直接去掉
    if date_str.endswith('Z'):
        date_str = date_str[:-1] + '+00:00'
    try:
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except:
        # 尝试去掉时区信息
        return datetime.fromisoformat(date_str.split('+')[0].split('Z')[0])

# 导入配置
try:
    from config import EMQX_CONFIG, SECRET_KEY, SQLALCHEMY_DATABASE_URI, MQTT_TOPICS
except ImportError:
    from config.example import EMQX_CONFIG, SECRET_KEY, SQLALCHEMY_DATABASE_URI, MQTT_TOPICS

# 导入 MQTT 客户端
from utils.mqtt.mqtt_client import MqttClient

# 创建 Flask 应用 - 同时服务前端静态文件
app = Flask(__name__, 
            static_folder='../frontend',
            static_url_path='',
            template_folder='../frontend')
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Session 配置 - 解决跨域认证问题
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# 启用 CORS - 允许携带凭证
CORS(app, supports_credentials=True, origins=['http://localhost:5000', 'http://127.0.0.1:5000', 'null'])

# 初始化数据库
db = SQLAlchemy(app)

# ============== 数据模型 ==============

class User(db.Model):
    """用户模型"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat()
        }


class Task(db.Model):
    """任务模型"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    completed = db.Column(db.Boolean, default=False)
    due_date = db.Column(db.DateTime, nullable=True)
    priority = db.Column(db.String(20), default='normal')  # low, normal, high
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'description': self.description,
            'completed': self.completed,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'priority': self.priority,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class CalendarEvent(db.Model):
    """日历事件模型"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=True)
    all_day = db.Column(db.Boolean, default=False)
    color = db.Column(db.String(20), default='#667eea')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'description': self.description,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'all_day': self.all_day,
            'color': self.color,
            'created_at': self.created_at.isoformat()
        }


# ============== MQTT 客户端 ==============

mqtt_client = None
mqtt_connected = False

def init_mqtt():
    """初始化 MQTT 客户端"""
    global mqtt_client, mqtt_connected
    
    config = {
        'broker': EMQX_CONFIG['broker'],
        'port': EMQX_CONFIG['port'],
        'client_id': f'todo_backend_{int(time.time())}',
        'username': EMQX_CONFIG['username'],
        'password': EMQX_CONFIG['password'],
        'use_tls': EMQX_CONFIG['use_tls'],
        'ca_cert': EMQX_CONFIG['ca_cert'],
        'qos': 1
    }
    
    mqtt_client = MqttClient(config)
    mqtt_client.connect()
    
    if mqtt_client.connected:
        mqtt_connected = True
        print("[MQTT] 后端已连接到 EMQX Cloud")
        
        # 订阅同步主题
        mqtt_client.subscribe([
            MQTT_TOPICS['tasks'],
            MQTT_TOPICS['sync']
        ], on_mqtt_message)
    else:
        print("[MQTT] 后端连接失败")


def on_mqtt_message(topic, message):
    """处理 MQTT 消息"""
    print(f"[MQTT] 收到消息: {topic} -> {message}")
    
    try:
        data = json.loads(message)
        
        if topic == MQTT_TOPICS['tasks']:
            # 处理任务同步
            handle_task_sync(data)
        elif topic == MQTT_TOPICS['sync']:
            # 处理同步请求
            handle_sync_request(data)
            
    except json.JSONDecodeError:
        print(f"[MQTT] 无效的 JSON 消息")
    except Exception as e:
        print(f"[MQTT] 处理消息错误: {e}")


def handle_task_sync(data):
    """处理任务同步"""
    with app.app_context():
        action = data.get('action')
        user_id = data.get('user_id')
        
        if action == 'update':
            task_id = data.get('task_id')
            task = Task.query.get(task_id)
            if task and task.user_id == user_id:
                # 广播更新给其他客户端
                publish_update('task_updated', task.to_dict())


def handle_sync_request(data):
    """处理同步请求"""
    with app.app_context():
        user_id = data.get('user_id')
        if user_id:
            tasks = Task.query.filter_by(user_id=user_id).all()
            publish_update('sync_response', {
                'user_id': user_id,
                'tasks': [t.to_dict() for t in tasks]
            })


def publish_update(event_type, data):
    """发布更新到 MQTT"""
    global mqtt_client, mqtt_connected
    
    if mqtt_connected and mqtt_client:
        message = json.dumps({
            'event': event_type,
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        })
        mqtt_client.publish(MQTT_TOPICS['sync'], message)


# ============== 用户认证 API ==============

@app.route('/api/auth/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    
    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400
    
    if User.query.filter_by(username=username).first():
        return jsonify({'error': '用户名已存在'}), 400
    
    user = User(username=username, email=email)
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    session['user_id'] = user.id
    
    return jsonify({
        'message': '注册成功',
        'user': user.to_dict()
    }), 201


@app.route('/api/auth/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400
    
    user = User.query.filter_by(username=username).first()
    
    if not user or not user.check_password(password):
        return jsonify({'error': '用户名或密码错误'}), 401
    
    session['user_id'] = user.id
    
    return jsonify({
        'message': '登录成功',
        'user': user.to_dict()
    })


@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """用户登出"""
    session.pop('user_id', None)
    return jsonify({'message': '已登出'})


@app.route('/api/auth/me', methods=['GET'])
def get_current_user():
    """获取当前登录用户"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'error': '未登录'}), 401
    
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    return jsonify({'user': user.to_dict()})


# ============== 任务 API ==============

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """获取当前用户的所有任务"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'error': '未登录'}), 401
    
    tasks = Task.query.filter_by(user_id=user_id).order_by(Task.created_at.desc()).all()
    
    return jsonify({
        'tasks': [t.to_dict() for t in tasks]
    })


@app.route('/api/tasks', methods=['POST'])
def create_task():
    """创建新任务"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'error': '未登录'}), 401
    
    data = request.get_json()
    
    task = Task(
        user_id=user_id,
        title=data.get('title'),
        description=data.get('description'),
        due_date=parse_datetime(data.get('due_date')),
        priority=data.get('priority', 'normal')
    )
    
    db.session.add(task)
    db.session.commit()
    
    # 通过 MQTT 广播新任务
    publish_update('task_created', task.to_dict())
    
    return jsonify({
        'message': '任务创建成功',
        'task': task.to_dict()
    }), 201


@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """更新任务"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'error': '未登录'}), 401
    
    task = Task.query.get(task_id)
    
    if not task:
        return jsonify({'error': '任务不存在'}), 404
    
    if task.user_id != user_id:
        return jsonify({'error': '无权限'}), 403
    
    data = request.get_json()
    
    if 'title' in data:
        task.title = data['title']
    if 'description' in data:
        task.description = data['description']
    if 'completed' in data:
        task.completed = data['completed']
    if 'due_date' in data:
        task.due_date = datetime.fromisoformat(data['due_date']) if data['due_date'] else None
    if 'priority' in data:
        task.priority = data['priority']
    
    db.session.commit()
    
    # 通过 MQTT 广播更新
    publish_update('task_updated', task.to_dict())
    
    return jsonify({
        'message': '任务更新成功',
        'task': task.to_dict()
    })


@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """删除任务"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'error': '未登录'}), 401
    
    task = Task.query.get(task_id)
    
    if not task:
        return jsonify({'error': '任务不存在'}), 404
    
    if task.user_id != user_id:
        return jsonify({'error': '无权限'}), 403
    
    task_data = task.to_dict()
    db.session.delete(task)
    db.session.commit()
    
    # 通过 MQTT 广播删除
    publish_update('task_deleted', task_data)
    
    return jsonify({
        'message': '任务删除成功',
        'task_id': task_id
    })


# ============== 日历 API ==============

@app.route('/api/calendar', methods=['GET'])
def get_calendar_events():
    """获取日历事件"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'error': '未登录'}), 401
    
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    
    query = CalendarEvent.query.filter_by(user_id=user_id)
    
    if start_date:
        query = query.filter(CalendarEvent.start_time >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(CalendarEvent.end_time <= datetime.fromisoformat(end_date))
    
    events = query.all()
    
    return jsonify({
        'events': [e.to_dict() for e in events]
    })


@app.route('/api/calendar', methods=['POST'])
def create_calendar_event():
    """创建日历事件"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'error': '未登录'}), 401
    
    data = request.get_json()
    
    event = CalendarEvent(
        user_id=user_id,
        title=data.get('title'),
        description=data.get('description'),
        start_time=parse_datetime(data.get('start_time')),
        end_time=parse_datetime(data.get('end_time')),
        all_day=data.get('all_day', False),
        color=data.get('color', '#667eea')
    )
    
    db.session.add(event)
    db.session.commit()
    
    return jsonify({
        'message': '事件创建成功',
        'event': event.to_dict()
    }), 201


@app.route('/api/calendar/<int:event_id>', methods=['PUT'])
def update_calendar_event(event_id):
    """更新日历事件"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'error': '未登录'}), 401
    
    event = CalendarEvent.query.get(event_id)
    
    if not event:
        return jsonify({'error': '事件不存在'}), 404
    
    if event.user_id != user_id:
        return jsonify({'error': '无权限'}), 403
    
    data = request.get_json()
    
    if 'title' in data:
        event.title = data['title']
    if 'description' in data:
        event.description = data['description']
    if 'start_time' in data:
        event.start_time = datetime.fromisoformat(data['start_time'])
    if 'end_time' in data:
        event.end_time = datetime.fromisoformat(data['end_time']) if data['end_time'] else None
    if 'all_day' in data:
        event.all_day = data['all_day']
    if 'color' in data:
        event.color = data['color']
    
    db.session.commit()
    
    return jsonify({
        'message': '事件更新成功',
        'event': event.to_dict()
    })


@app.route('/api/calendar/<int:event_id>', methods=['DELETE'])
def delete_calendar_event(event_id):
    """删除日历事件"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'error': '未登录'}), 401
    
    event = CalendarEvent.query.get(event_id)
    
    if not event:
        return jsonify({'error': '事件不存在'}), 404
    
    if event.user_id != user_id:
        return jsonify({'error': '无权限'}), 403
    
    db.session.delete(event)
    db.session.commit()
    
    return jsonify({
        'message': '事件删除成功',
        'event_id': event_id
    })


# ============== 统计 API ==============

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """获取统计数据"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'error': '未登录'}), 401
    
    total_tasks = Task.query.filter_by(user_id=user_id).count()
    completed_tasks = Task.query.filter_by(user_id=user_id, completed=True).count()
    pending_tasks = total_tasks - completed_tasks
    
    # 今日到期任务
    today = datetime.utcnow().date()
    due_today = Task.query.filter_by(user_id=user_id).filter(
        db.func.date(Task.due_date) == today
    ).count()
    
    # 高优先级任务
    high_priority = Task.query.filter_by(user_id=user_id, priority='high', completed=False).count()
    
    return jsonify({
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'due_today': due_today,
        'high_priority': high_priority
    })


# ============== 前端页面路由 ==============

@app.route('/')
def index():
    """返回前端页面"""
    return app.send_static_file('index.html')


# ============== 主程序 ==============

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("[数据库] 表已创建")
    
    # 初始化 MQTT
    init_mqtt()
    
    print("[服务器] 启动中...")
    app.run(host='0.0.0.0', port=5000, debug=True)