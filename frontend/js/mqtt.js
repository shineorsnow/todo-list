// MQTT 前端模块 - 使用 WebSocket 连接
const MQTT = {
    client: null,
    connected: false,
    reconnectInterval: null,
    
    // 连接到 MQTT 代理
    connect(onMessage) {
        return new Promise((resolve, reject) => {
            try {
                // 使用浏览器原生 WebSocket
                // 注意：需要引入 mqtt.js 库
                if (typeof mqtt === 'undefined') {
                    console.warn('[MQTT] mqtt.js 库未加载，使用模拟模式');
                    this.simulateConnect(onMessage);
                    resolve();
                    return;
                }
                
                const options = {
                    clientId: 'todo_frontend_' + Math.random().toString(16).substr(2, 8),
                    username: CONFIG.MQTT.username,
                    password: CONFIG.MQTT.password,
                    clean: true,
                    reconnectPeriod: 5000
                };
                
                this.client = mqtt.connect(CONFIG.MQTT.broker, options);
                
                this.client.on('connect', () => {
                    this.connected = true;
                    console.log('[MQTT] 已连接到 EMQX Cloud');
                    this.updateStatus(true);
                    
                    // 订阅主题
                    this.client.subscribe(Object.values(CONFIG.MQTT.topics), (err) => {
                        if (err) {
                            console.error('[MQTT] 订阅失败:', err);
                        } else {
                            console.log('[MQTT] 已订阅主题');
                        }
                    });
                    
                    resolve();
                });
                
                this.client.on('message', (topic, message) => {
                    const msg = message.toString();
                    console.log(`[MQTT] 收到消息: ${topic} -> ${msg}`);
                    if (onMessage) {
                        try {
                            const data = JSON.parse(msg);
                            onMessage(topic, data);
                        } catch (e) {
                            onMessage(topic, msg);
                        }
                    }
                });
                
                this.client.on('error', (err) => {
                    console.error('[MQTT] 错误:', err);
                    this.updateStatus(false);
                });
                
                this.client.on('close', () => {
                    this.connected = false;
                    console.log('[MQTT] 连接关闭');
                    this.updateStatus(false);
                });
                
                this.client.on('reconnect', () => {
                    console.log('[MQTT] 正在重连...');
                });
                
            } catch (error) {
                console.error('[MQTT] 连接失败:', error);
                this.simulateConnect(onMessage);
                resolve();
            }
        });
    },
    
    // 模拟连接（当 mqtt.js 不可用时）
    simulateConnect(onMessage) {
        this.connected = true;
        this.updateStatus(true);
        console.log('[MQTT] 模拟模式启动');
        
        // 模拟接收消息
        this.simulateCallback = onMessage;
    },
    
    // 发布消息
    publish(topic, message) {
        if (this.client && this.connected) {
            const msg = typeof message === 'string' ? message : JSON.stringify(message);
            this.client.publish(topic, msg);
            console.log(`[MQTT] 已发布: ${topic} -> ${msg}`);
        } else {
            console.warn('[MQTT] 未连接，无法发布消息');
        }
    },
    
    // 断开连接
    disconnect() {
        if (this.client) {
            this.client.end();
            this.connected = false;
            this.updateStatus(false);
            console.log('[MQTT] 已断开连接');
        }
    },
    
    // 更新状态显示
    updateStatus(connected) {
        const indicator = document.getElementById('mqttIndicator');
        const status = document.getElementById('mqttStatus');
        
        if (indicator) {
            indicator.className = 'indicator ' + (connected ? 'online' : 'offline');
        }
        if (status) {
            status.textContent = 'MQTT: ' + (connected ? '已连接' : '未连接');
        }
    }
};