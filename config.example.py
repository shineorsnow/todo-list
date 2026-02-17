# 配置文件示例
# 复制此文件为 config.py 并填入实际值

# EMQX Cloud 配置
EMQX_CONFIG = {
    'broker': 'your-broker-address.emqxsl.cn',
    'port': 8883,
    'username': 'your-username',
    'password': 'your-password',
    'use_tls': True,
    'ca_cert': 'emqxsl-ca.crt',  # CA证书路径
}

# Flask 配置
SECRET_KEY = 'your-secret-key-change-in-production'

# 数据库配置
SQLALCHEMY_DATABASE_URI = 'sqlite:///todo.db'

# MQTT 主题
MQTT_TOPICS = {
    'tasks': 'todo/tasks',
    'calendar': 'todo/calendar',
    'sync': 'todo/sync',
}