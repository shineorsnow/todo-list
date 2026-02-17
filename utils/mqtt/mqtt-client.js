/**
 * MQTT 客户端 - JavaScript (Node.js)
 * 
 * 依赖安装: npm install mqtt
 * 运行: node mqtt-client.js
 */

const mqtt = require('mqtt');

// ============== 配置区域 ==============
const CONFIG = {
    broker: 'tcp://localhost:1883',  // MQTT 代理地址
    clientId: 'mqtt_js_client_' + Math.random().toString(16).substr(2, 8),
    username: '',  // 用户名（如果需要）
    password: '',  // 密码（如果需要）
    topic: 'test/topic',
    qos: 1
};
// =====================================

class MqttClient {
    constructor(config) {
        this.config = config;
        this.client = null;
    }

    /**
     * 连接到 MQTT 代理
     */
    connect() {
        const options = {
            clientId: this.config.clientId,
            clean: true,
            connectTimeout: 4000,
            reconnectPeriod: 1000
        };

        if (this.config.username) {
            options.username = this.config.username;
        }
        if (this.config.password) {
            options.password = this.config.password;
        }

        this.client = mqtt.connect(this.config.broker, options);

        this.client.on('connect', () => {
            console.log(`[已连接] 连接到代理: ${this.config.broker}`);
        });

        this.client.on('error', (err) => {
            console.error(`[错误] ${err.message}`);
        });

        this.client.on('close', () => {
            console.log('[已断开] 连接已关闭');
        });

        return this;
    }

    /**
     * 发布消息
     * @param {string} topic - 主题
     * @param {string|object} message - 消息内容
     * @param {number} qos - 服务质量等级 (0, 1, 2)
     */
    publish(topic, message, qos = this.config.qos) {
        if (!this.client || !this.client.connected) {
            console.error('[错误] 客户端未连接');
            return;
        }

        const payload = typeof message === 'object' ? JSON.stringify(message) : message;
        
        this.client.publish(topic, payload, { qos }, (err) => {
            if (err) {
                console.error(`[发布失败] ${err.message}`);
            } else {
                console.log(`[已发布] 主题: ${topic}, 消息: ${payload}`);
            }
        });
    }

    /**
     * 订阅主题
     * @param {string|Array} topics - 主题或主题数组
     * @param {function} callback - 消息回调函数
     */
    subscribe(topics, callback) {
        if (!this.client || !this.client.connected) {
            console.error('[错误] 客户端未连接');
            return;
        }

        const topicList = Array.isArray(topics) ? topics : [topics];
        
        this.client.subscribe(topicList, { qos: this.config.qos }, (err) => {
            if (err) {
                console.error(`[订阅失败] ${err.message}`);
            } else {
                console.log(`[已订阅] 主题: ${topicList.join(', ')}`);
            }
        });

        // 监听消息
        this.client.on('message', (topic, message) => {
            const msg = message.toString();
            console.log(`[收到消息] 主题: ${topic}, 消息: ${msg}`);
            if (callback) {
                callback(topic, msg);
            }
        });
    }

    /**
     * 取消订阅
     * @param {string|Array} topics - 主题或主题数组
     */
    unsubscribe(topics) {
        if (!this.client || !this.client.connected) {
            console.error('[错误] 客户端未连接');
            return;
        }

        const topicList = Array.isArray(topics) ? topics : [topics];
        
        this.client.unsubscribe(topicList, (err) => {
            if (err) {
                console.error(`[取消订阅失败] ${err.message}`);
            } else {
                console.log(`[已取消订阅] 主题: ${topicList.join(', ')}`);
            }
        });
    }

    /**
     * 断开连接
     */
    disconnect() {
        if (this.client) {
            this.client.end();
            console.log('[已断开] 客户端已断开连接');
        }
    }
}

// ============== 使用示例 ==============
if (require.main === module) {
    const mqttClient = new MqttClient(CONFIG);
    
    // 连接
    mqttClient.connect();
    
    // 连接成功后执行操作
    setTimeout(() => {
        // 订阅主题
        mqttClient.subscribe(CONFIG.topic, (topic, message) => {
            console.log(`回调收到: ${topic} -> ${message}`);
        });
        
        // 发布消息
        mqttClient.publish(CONFIG.topic, 'Hello MQTT from Node.js!');
        mqttClient.publish(CONFIG.topic, { type: 'json', data: 'test' });
    }, 2000);
    
    // 10秒后断开
    setTimeout(() => {
        mqttClient.disconnect();
    }, 10000);
}

module.exports = MqttClient;