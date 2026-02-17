// 前端配置
const CONFIG = {
    // 后端 API 地址
    API_BASE: 'http://localhost:5000/api',
    
    // MQTT 配置 - WebSocket 连接
    MQTT: {
        broker: 'wss://d6c1f93c.ala.cn-hangzhou.emqxsl.cn:8084/mqtt',
        username: 'test',
        password: '1111',
        topics: {
            tasks: 'todo/tasks',
            calendar: 'todo/calendar',
            sync: 'todo/sync',
            notification: 'todo/notification'
        }
    }
};