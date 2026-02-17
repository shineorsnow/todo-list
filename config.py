# 实际配置文件 - 包含敏感信息，已在 .gitignore 中
# EMQX Cloud 配置
EMQX_CONFIG = {
    'broker': 'd6c1f93c.ala.cn-hangzhou.emqxsl.cn',
    'port': 8883,
    'username': 'test',
    'password': '1111',
    'use_tls': True,
    'ca_cert': 'emqxsl-ca.crt',
}

# Flask 配置
SECRET_KEY = 'todo-secret-key-2026'

# 数据库配置
SQLALCHEMY_DATABASE_URI = 'sqlite:///todo.db'

# MQTT 主题
MQTT_TOPICS = {
    'tasks': 'todo/tasks',
    'calendar': 'todo/calendar',
    'sync': 'todo/sync',
    'notification': 'todo/notification',
}