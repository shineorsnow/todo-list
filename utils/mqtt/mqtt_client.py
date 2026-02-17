"""
MQTT 客户端 - Python

依赖安装: pip install paho-mqtt
运行: python mqtt_client.py
"""

import json
import time
import random
import paho.mqtt.client as mqtt

# ============== 配置区域 ==============
CONFIG = {
    'broker': 'localhost',
    'port': 1883,
    'client_id': f'mqtt_python_client_{random.randint(0, 1000)}',
    'username': '',  # 用户名（如果需要）
    'password': '',  # 密码（如果需要）
    'topic': 'test/topic',
    'qos': 1
}
# =====================================


class MqttClient:
    """MQTT 客户端类"""
    
    def __init__(self, config: dict):
        self.config = config
        self.client = mqtt.Client(client_id=config['client_id'])
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
    
    def _on_connect(self, client, userdata, flags, rc):
        """连接回调"""
        if rc == 0:
            self.connected = True
            print(f"[已连接] 连接到代理: {self.config['broker']}:{self.config['port']}")
        else:
            print(f"[连接失败] 返回码: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """断开回调"""
        self.connected = False
        print(f"[已断开] 连接已关闭, 返回码: {rc}")
    
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
            time.sleep(1)
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
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
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
        
        if result == mqtt.MQTT_ERR_SUCCESS:
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
        
        if result == mqtt.MQTT_ERR_SUCCESS:
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
    mqtt_client = MqttClient(CONFIG)
    
    # 连接
    mqtt_client.connect()
    
    # 等待连接建立
    time.sleep(1)
    
    # 订阅主题
    def on_message(topic, message):
        print(f"回调收到: {topic} -> {message}")
    
    mqtt_client.subscribe(CONFIG['topic'], callback=on_message)
    
    # 发布消息
    mqtt_client.publish(CONFIG['topic'], 'Hello MQTT from Python!')
    mqtt_client.publish(CONFIG['topic'], {'type': 'json', 'data': 'test'})
    
    # 保持运行
    try:
        time.sleep(10)
    except KeyboardInterrupt:
        pass
    
    # 断开连接
    mqtt_client.disconnect()