"""
EMQX Cloud 连接测试 - Python

测试连接到 EMQX Cloud 服务器
连接地址: d6c1f93c.ala.cn-hangzhou.emqxsl.cn
端口: 8883 (TLS)
CA证书: ./emqxsl-ca.crt

运行: python test_emqx.py
"""

import ssl
import time
import random
from paho.mqtt.client import Client, CallbackAPIVersion

# ============== 配置区域 ==============
CONFIG = {
    'broker': 'd6c1f93c.ala.cn-hangzhou.emqxsl.cn',
    'port': 8883,
    'client_id': f'emqx_test_client_{random.randint(0, 10000)}',
    'username': 'test',  # EMQX Cloud 认证用户名
    'password': '1111',  # EMQX Cloud 认证密码
    'topic': 'test/topic',
    'qos': 1,
    'ca_cert': 'w:/代办清单/emqxsl-ca.crt',  # CA 证书绝对路径
}
# =====================================


class EmqxTestClient:
    """EMQX Cloud 测试客户端"""
    
    def __init__(self, config: dict):
        self.config = config
        # paho-mqtt 2.x 需要指定 CallbackAPIVersion
        self.client = Client(callback_api_version=CallbackAPIVersion.VERSION2, 
                            client_id=config['client_id'])
        self.connected = False
        self.connect_error = None
        
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
        self._setup_tls()
    
    def _setup_tls(self):
        """设置 TLS/SSL 连接"""
        try:
            # 使用 CA 证书验证服务器
            self.client.tls_set(
                ca_certs=self.config['ca_cert'],
                cert_reqs=ssl.CERT_REQUIRED,
                tls_version=ssl.PROTOCOL_TLS
            )
            print(f"[TLS设置] 使用 CA 证书: {self.config['ca_cert']}")
        except Exception as e:
            print(f"[TLS错误] {e}")
            # 如果证书文件不存在，尝试跳过证书验证（不推荐生产环境使用）
            print("[警告] 跳过证书验证（仅用于测试）")
            self.client.tls_set(cert_reqs=ssl.CERT_NONE)
            self.client.tls_insecure_set(True)
    
    def _on_connect(self, client, userdata, flags, rc, properties=None):
        """连接回调"""
        # paho-mqtt 2.x 中 rc 是 ReasonCode 对象
        rc_value = rc.value if hasattr(rc, 'value') else rc
        
        if rc_value == 0:
            self.connected = True
            print(f"[✓ 已连接] 成功连接到 EMQX Cloud: {self.config['broker']}:{self.config['port']}")
        else:
            self.connect_error = rc_value
            error_msgs = {
                1: "协议版本不正确",
                2: "客户端标识符无效",
                3: "服务器不可用",
                4: "用户名或密码错误",
                5: "未授权"
            }
            print(f"[✗ 连接失败] 返回码: {rc_value}, 原因: {error_msgs.get(rc_value, str(rc))}")
            print(f"[提示] 如果返回码为 5，请检查 EMQX Cloud 是否需要认证")
    
    def _on_disconnect(self, client, userdata, disconnect_flags, rc, properties=None):
        """断开回调"""
        self.connected = False
        rc_value = rc.value if hasattr(rc, 'value') else rc
        print(f"[已断开] 连接已关闭, 返回码: {rc_value}")
    
    def _on_message(self, client, userdata, msg):
        """消息回调"""
        payload = msg.payload.decode('utf-8')
        print(f"[✓ 收到消息] 主题: {msg.topic}, 消息: {payload}")
    
    def connect(self):
        """连接到 EMQX Cloud"""
        try:
            print(f"[连接中...] 正在连接 {self.config['broker']}:{self.config['port']}")
            self.client.connect(
                self.config['broker'], 
                self.config['port'], 
                keepalive=60
            )
            self.client.loop_start()
            # 等待连接建立
            timeout = 10
            start = time.time()
            while not self.connected and (time.time() - start) < timeout:
                if self.connect_error is not None:
                    break
                time.sleep(0.1)
            
            if not self.connected:
                if self.connect_error:
                    print(f"[✗ 连接被拒绝]")
                else:
                    print("[✗ 连接超时]")
                
        except Exception as e:
            print(f"[✗ 连接错误] {e}")
        
        return self
    
    def publish(self, topic: str, message: str) -> bool:
        """发布消息"""
        if not self.connected:
            print("[✗ 错误] 客户端未连接")
            return False
        
        result = self.client.publish(topic, message, qos=self.config['qos'])
        
        if result.rc == 0:
            print(f"[✓ 已发布] 主题: {topic}, 消息: {message}")
            return True
        else:
            print(f"[✗ 发布失败] 错误码: {result.rc}")
            return False
    
    def subscribe(self, topic: str):
        """订阅主题"""
        if not self.connected:
            print("[✗ 错误] 客户端未连接")
            return
        
        result, mid = self.client.subscribe(topic, qos=self.config['qos'])
        
        if result == 0:
            print(f"[✓ 已订阅] 主题: {topic}")
        else:
            print(f"[✗ 订阅失败] 错误码: {result}")
    
    def disconnect(self):
        """断开连接"""
        self.client.loop_stop()
        self.client.disconnect()
        print("[已断开] 客户端已断开连接")


def main():
    print("=" * 50)
    print("EMQX Cloud 连接测试")
    print("=" * 50)
    print(f"服务器: {CONFIG['broker']}")
    print(f"端口: {CONFIG['port']} (TLS)")
    print(f"客户端ID: {CONFIG['client_id']}")
    print(f"用户名: {CONFIG['username'] or '(未设置)'}")
    print("=" * 50)
    
    # 创建测试客户端
    test_client = EmqxTestClient(CONFIG)
    
    # 连接
    test_client.connect()
    
    if test_client.connected:
        print("\n" + "-" * 50)
        print("开始测试发布和订阅...")
        print("-" * 50)
        
        # 订阅主题
        test_client.subscribe(CONFIG['topic'])
        time.sleep(0.5)
        
        # 发布多条测试消息
        for i in range(3):
            test_client.publish(CONFIG['topic'], f"测试消息 #{i+1} 来自 Python 客户端")
            time.sleep(0.5)
        
        # 等待接收消息
        print("\n等待接收消息...")
        time.sleep(3)
        
        # 测试完成
        print("\n" + "-" * 50)
        print("测试完成！连接和消息收发正常。")
        print("-" * 50)
    else:
        print("\n" + "-" * 50)
        print("连接失败！可能的原因：")
        print("1. EMQX Cloud 需要用户名密码认证")
        print("2. 证书路径不正确")
        print("3. 网络连接问题")
        print("-" * 50)
        print("\n请在 CONFIG 中设置正确的用户名和密码后重试")
    
    # 断开连接
    test_client.disconnect()


if __name__ == '__main__':
    main()