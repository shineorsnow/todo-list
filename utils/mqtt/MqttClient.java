import org.eclipse.paho.client.mqttv3.*;
import org.eclipse.paho.client.mqttv3.persist.MemoryPersistence;
import com.google.gson.Gson;

/**
 * MQTT 客户端 - Java
 * 
 * Maven 依赖:
 * <dependency>
 *     <groupId>org.eclipse.paho</groupId>
 *     <artifactId>org.eclipse.paho.client.mqttv3</artifactId>
 *     <version>1.2.5</version>
 * </dependency>
 * 
 * 编译运行:
 * mvn compile exec:java -Dexec.mainClass="MqttClient"
 */

public class MqttClient {
    
    // ============== 配置区域 ==============
    private static final String BROKER = "tcp://localhost:1883";
    private static final String CLIENT_ID = "mqtt_java_client_" + System.currentTimeMillis();
    private static final String USERNAME = "";  // 用户名（如果需要）
    private static final String PASSWORD = "";  // 密码（如果需要）
    private static final String TOPIC = "test/topic";
    private static final int QOS = 1;
    // =====================================
    
    private IMqttAsyncClient client;
    private Gson gson = new Gson();
    private MessageCallback messageCallback;
    
    /**
     * 消息回调接口
     */
    public interface MessageCallback {
        void onMessage(String topic, String message);
    }
    
    /**
     * 连接到 MQTT 代理
     */
    public MqttClient connect() {
        try {
            MemoryPersistence persistence = new MemoryPersistence();
            client = new MqttAsyncClient(BROKER, CLIENT_ID, persistence);
            
            // 设置回调
            client.setCallback(new MqttCallback() {
                @Override
                public void connectionLost(Throwable cause) {
                    System.out.println("[已断开] 连接丢失: " + cause.getMessage());
                }
                
                @Override
                public void messageArrived(String topic, MqttMessage message) throws Exception {
                    String payload = new String(message.getPayload());
                    System.out.println("[收到消息] 主题: " + topic + ", 消息: " + payload);
                    
                    if (messageCallback != null) {
                        messageCallback.onMessage(topic, payload);
                    }
                }
                
                @Override
                public void deliveryComplete(IMqttDeliveryToken token) {
                    // 消息发送完成
                }
            });
            
            // 连接选项
            MqttConnectOptions options = new MqttConnectOptions();
            options.setCleanSession(true);
            options.setConnectionTimeout(10);
            options.setKeepAliveInterval(60);
            
            if (!USERNAME.isEmpty()) {
                options.setUserName(USERNAME);
            }
            if (!PASSWORD.isEmpty()) {
                options.setPassword(PASSWORD.toCharArray());
            }
            
            // 连接
            client.connect(options).waitForCompletion();
            System.out.println("[已连接] 连接到代理: " + BROKER);
            
        } catch (MqttException e) {
            System.err.println("[连接错误] " + e.getMessage());
        }
        
        return this;
    }
    
    /**
     * 发布消息
     * @param topic 主题
     * @param message 消息内容
     * @param qos 服务质量等级 (0, 1, 2)
     */
    public void publish(String topic, Object message, int qos) {
        if (client == null || !client.isConnected()) {
            System.err.println("[错误] 客户端未连接");
            return;
        }
        
        try {
            String payload;
            if (message instanceof String) {
                payload = (String) message;
            } else {
                payload = gson.toJson(message);
            }
            
            MqttMessage mqttMessage = new MqttMessage(payload.getBytes());
            mqttMessage.setQos(qos);
            
            client.publish(topic, mqttMessage).waitForCompletion();
            System.out.println("[已发布] 主题: " + topic + ", 消息: " + payload);
            
        } catch (MqttException e) {
            System.err.println("[发布失败] " + e.getMessage());
        }
    }
    
    /**
     * 发布消息（使用默认 QOS）
     */
    public void publish(String topic, Object message) {
        publish(topic, message, QOS);
    }
    
    /**
     * 订阅主题
     * @param topics 主题数组
     * @param callback 消息回调
     */
    public void subscribe(String[] topics, MessageCallback callback) {
        if (client == null || !client.isConnected()) {
            System.err.println("[错误] 客户端未连接");
            return;
        }
        
        this.messageCallback = callback;
        
        try {
            int[] qos = new int[topics.length];
            for (int i = 0; i < topics.length; i++) {
                qos[i] = QOS;
            }
            
            client.subscribe(topics, qos).waitForCompletion();
            System.out.println("[已订阅] 主题: " + String.join(", ", topics));
            
        } catch (MqttException e) {
            System.err.println("[订阅失败] " + e.getMessage());
        }
    }
    
    /**
     * 订阅单个主题
     */
    public void subscribe(String topic, MessageCallback callback) {
        subscribe(new String[]{topic}, callback);
    }
    
    /**
     * 取消订阅
     * @param topics 主题数组
     */
    public void unsubscribe(String[] topics) {
        if (client == null || !client.isConnected()) {
            System.err.println("[错误] 客户端未连接");
            return;
        }
        
        try {
            client.unsubscribe(topics).waitForCompletion();
            System.out.println("[已取消订阅] 主题: " + String.join(", ", topics));
            
        } catch (MqttException e) {
            System.err.println("[取消订阅失败] " + e.getMessage());
        }
    }
    
    /**
     * 断开连接
     */
    public void disconnect() {
        if (client != null && client.isConnected()) {
            try {
                client.disconnect().waitForCompletion();
                client.close();
                System.out.println("[已断开] 客户端已断开连接");
            } catch (MqttException e) {
                System.err.println("[断开错误] " + e.getMessage());
            }
        }
    }
    
    /**
     * 检查是否已连接
     */
    public boolean isConnected() {
        return client != null && client.isConnected();
    }
    
    // ============== 使用示例 ==============
    public static void main(String[] args) throws InterruptedException {
        MqttClient mqttClient = new MqttClient();
        
        // 连接
        mqttClient.connect();
        
        // 等待连接建立
        Thread.sleep(1000);
        
        // 订阅主题
        mqttClient.subscribe(TOPIC, (topic, message) -> {
            System.out.println("回调收到: " + topic + " -> " + message);
        });
        
        // 发布消息
        mqttClient.publish(TOPIC, "Hello MQTT from Java!");
        mqttClient.publish(TOPIC, new TestData("json", "test"));
        
        // 保持运行
        Thread.sleep(10000);
        
        // 断开连接
        mqttClient.disconnect();
    }
    
    // 测试数据类
    static class TestData {
        String type;
        String data;
        
        TestData(String type, String data) {
            this.type = type;
            this.data = data;
        }
    }
}