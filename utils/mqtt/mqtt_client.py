"""
MQTT 客户端 - Python

依赖安装: pip install paho-mqtt
运行: python mqtt_client.py

支持:
- 普通连接 (tcp://host:1883)
- TLS/SSL 连接 (ssl://host:8883)
- EMQX Cloud 等云服务
"""

import ssl
import json
import time
import random
from paho.mqtt.client import Client, CallbackAPIVersion

# ============== 配置区域 ==============
CONFIG = {
    'broker': 'localhost',
    'port': 1883,
    'client_id': f'mqtt_python_client_{random.randint(0, 1000)}',
    'username': '',  # 用户名（如果需要）
    'password': '',  # 密码（如果需要）
    'topic': 'test/topic',
    'qos': 1,
    # TLS 配置
    'use_tls': False,
    'ca_cert': None,  # CA 证书路径
    'insecure': False,  # 是否跳过证书验证
}
# =====================================


class MqttClient:
    """MQTT 客户端类"""
    
    def __init__(self, config: dict):
        self.config = config
        # paho-mqtt 2.x 需要指定 CallbackAPIVersion
        self.client = Client(
            callback_api_version=CallbackAPIVersion.VERSION2,
            client_id=config['client_id']
        )
        self.connected = False
        
        # 设置回调
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        
        # 设置认证信息
        if config.get('username'):
            self.client.username_pw_set(
                config['username'], 
                config.get('password', '')
            )
        
        # 设置 TLS
        if config.get('use_tls'):
            self._setup_tls()
    
    def _setup_tls(self):
        """设置 TLS/SSL 连接"""
        try:
            if self.config.get('ca_cert'):
                # 使用 CA 证书验证服务器
                self.client.tls_set(
                    ca_certs=self.config['ca_cert'],
                    cert_reqs=ssl.CERT_REQUIRED,
                    tls_version=ssl.PROTOCOL_TLS
                )
                print(f"[TLS] 使用 CA 证书: {self.config['ca_cert']}")
            else:
                # 无 CA 证书
                if self.config.get('insecure'):
                    self.client.tls_set(cert_reqs=ssl.CERT_NONE)
                    self.client.tls_insecure_set(True)
                    print("[TLS] 跳过证书验证")
                else:
                    self.client.tls_set(cert_reqs=ssl.CERT_REQUIRED)
                    print("[TLS] 使用系统默认证书")
        except Exception as e:
            print(f"[TLS错误] {e}")
    
    def _on_connect(self, client, userdata, flags, rc, properties=None):
        """连接回调"""
        rc_value = rc.value if hasattr(rc, 'value') else rc
        
        if rc_value == 0:
            self.connected = True
            print(f"[已连接] 连接到代理: {self.config['broker']}:{self.config['port']}")
        else:
            error_msgs = {
                1: "协议版本不正确",
                2: "客户端标识符无效",
                3: "服务器不可用",
                4: "用户名或密码错误",
                5: "未授权"
            }
            print(f"[连接失败] 返回码: {rc_value}, 原因: {error_msgs.get(rc_value, '未知错误')}")
    
    def _on_disconnect(self, client, userdata, disconnect_flags, rc, properties=None):
        """断开回调"""
        self.connected = False
        rc_value = rc.value if hasattr(rc, 'value') else rc
        print(f"[已断开] 连接已关闭, 返回码: {rc_value}")
    
    def _on_message(self, client, userdata, msg):
        """消息回调"""
        payload = msg.payload.decode('utf-8')
        print(f"[收到消息] 主题: {msg.topic}, 消息: {payload}")
        
        # 如果有自定义回调，调用它
        if hasattr(self, 'message_callback') and self.message_callback:
            self.message_callback(msg.topic, payload)
    
    def connect(self):
        """连接到 MQTT 代理"""
        try:
            self.client.connect(
                self.config['broker'], 
                self.config['port'], 
                keepalive=60
            )
            self.client.loop_start()
            # 等待连接建立
            timeout = 5
            start = time.time()
            while not self.connected and (time.time() - start) < timeout:
                time.sleep(0.1)
        except Exception as e:
            print(f"[连接错误] {e}")
        
        return self
    
    def publish(self, topic: str, message, qos: int = None):
        """
        发布消息
        
        Args:
            topic: 主题
            message: 消息内容（字符串或字典）
            qos: 服务质量等级 (0, 1, 2)
        """
        if not self.connected:
            print("[错误] 客户端未连接")
            return
        
        if qos is None:
            qos = self.config['qos']
        
        # 处理消息
        if isinstance(message, (dict, list)):
            payload = json.dumps(message, ensure_ascii=False)
        else:
            payload = str(message)
        
        result = self.client.publish(topic, payload, qos=qos)
        
        if result.rc == 0:
            print(f"[已发布] 主题: {topic}, 消息: {payload}")
        else:
            print(f"[发布失败] 错误码: {result.rc}")
    
    def subscribe(self, topics, callback=None):
        """
        订阅主题
        
        Args:
            topics: 主题字符串或主题列表
            callback: 消息回调函数
        """
        if not self.connected:
            print("[错误] 客户端未连接")
            return
        
        # 保存回调
        self.message_callback = callback
        
        # 处理主题
        if isinstance(topics, str):
            topic_list = [(topics, self.config['qos'])]
        else:
            topic_list = [(t, self.config['qos']) for t in topics]
        
        result, mid = self.client.subscribe(topic_list)
        
        if result == 0:
            topic_names = [t[0] for t in topic_list]
            print(f"[已订阅] 主题: {', '.join(topic_names)}")
        else:
            print(f"[订阅失败] 错误码: {result}")
    
    def unsubscribe(self, topics):
        """
        取消订阅
        
        Args:
            topics: 主题字符串或主题列表
        """
        if not self.connected:
            print("[错误] 客户端未连接")
            return
        
        if isinstance(topics, str):
            topics = [topics]
        
        result, mid = self.client.unsubscribe(topics)
        
        if result == 0:
            print(f"[已取消订阅] 主题: {', '.join(topics)}")
        else:
            print(f"[取消订阅失败] 错误码: {result}")
    
    def disconnect(self):
        """断开连接"""
        self.client.loop_stop()
        self.client.disconnect()
        print("[已断开] 客户端已断开连接")


# ============== 使用示例 ==============
if __name__ == '__main__':
    # 示例1: 普通连接
    print("=== 普通连接示例 ===")
    mqtt_client = MqttClient(CONFIG)
    
    # 连接
    mqtt_client.connect()
    
    if mqtt_client.connected:
        # 订阅主题
        def on_message(topic, message):
            print(f"回调收到: {topic} -> {message}")
        
        mqtt_client.subscribe(CONFIG['topic'], callback=on_message)
        
        # 发布消息
        mqtt_client.publish(CONFIG['topic'], 'Hello MQTT from Python!')
        mqtt_client.publish(CONFIG['topic'], {'type': 'json', 'data': 'test'})
        
        # 保持运行
        time.sleep(5)
        
        # 断开连接
        mqtt_client.disconnect()


# ============== EMQX Cloud 连接示例 ==============
"""
# EMQX Cloud TLS 连接配置
EMQX_CONFIG = {
    'broker': 'd6c1f93c.ala.cn-hangzhou.emqxsl.cn',
    'port': 8883,
    'client_id': f'emqx_client_{random.randint(0, 10000)}',
    'username': 'test',
    'password': '1111',
    'topic': 'test/topic',
    'qos': 1,
    'use_tls': True,
    'ca_cert': 'emqxsl-ca.crt',  # CA 证书路径
}

# 使用
client = MqttClient(EMQX_CONFIG)
client.connect()
client.subscribe('test/topic')
client.publish('test/topic', 'Hello EMQX!')
"""