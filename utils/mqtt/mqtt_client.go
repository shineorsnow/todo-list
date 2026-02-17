// MQTT 客户端 - Go
//
// 依赖安装: go get github.com/eclipse/paho.mqtt.golang
// 运行: go run mqtt_client.go

package main

import (
	"encoding/json"
	"fmt"
	"os"
	"os/signal"
	"syscall"
	"time"

	mqtt "github.com/eclipse/paho.mqtt.golang"
)

// ============== 配置区域 ==============
var config = MqttConfig{
	Broker:   "tcp://localhost:1883",
	ClientID: fmt.Sprintf("mqtt_go_client_%d", time.Now().Unix()),
	Username: "", // 用户名（如果需要）
	Password: "", // 密码（如果需要）
	Topic:    "test/topic",
	Qos:      byte(1),
}

// MqttConfig MQTT 配置结构
type MqttConfig struct {
	Broker   string
	ClientID string
	Username string
	Password string
	Topic    string
	Qos      byte
}

// =====================================

// MqttClient MQTT 客户端
type MqttClient struct {
	client mqtt.Client
	config MqttConfig
}

// MessageHandler 消息处理函数类型
type MessageHandler func(topic string, message string)

// NewMqttClient 创建新的 MQTT 客户端
func NewMqttClient(config MqttConfig) *MqttClient {
	return &MqttClient{
		config: config,
	}
}

// Connect 连接到 MQTT 代理
func (m *MqttClient) Connect() *MqttClient {
	opts := mqtt.NewClientOptions()
	opts.AddBroker(m.config.Broker)
	opts.SetClientID(m.config.ClientID)
	opts.SetCleanSession(true)
	opts.SetAutoReconnect(true)

	if m.config.Username != "" {
		opts.SetUsername(m.config.Username)
	}
	if m.config.Password != "" {
		opts.SetPassword(m.config.Password)
	}

	// 设置连接回调
	opts.OnConnect = func(c mqtt.Client) {
		fmt.Printf("[已连接] 连接到代理: %s\n", m.config.Broker)
	}

	opts.OnConnectionLost = func(c mqtt.Client, err error) {
		fmt.Printf("[已断开] 连接丢失: %v\n", err)
	}

	m.client = mqtt.NewClient(opts)

	if token := m.client.Connect(); token.Wait() && token.Error() != nil {
		fmt.Printf("[连接错误] %v\n", token.Error())
	}

	return m
}

// Publish 发布消息
func (m *MqttClient) Publish(topic string, message interface{}, qos ...byte) {
	if !m.client.IsConnected() {
		fmt.Println("[错误] 客户端未连接")
		return
	}

	q := m.config.Qos
	if len(qos) > 0 {
		q = qos[0]
	}

	var payload string
	switch v := message.(type) {
	case string:
		payload = v
	default:
		bytes, err := json.Marshal(v)
		if err != nil {
			fmt.Printf("[序列化错误] %v\n", err)
			return
		}
		payload = string(bytes)
	}

	token := m.client.Publish(topic, q, false, payload)
	token.Wait()

	if token.Error() != nil {
		fmt.Printf("[发布失败] %v\n", token.Error())
	} else {
		fmt.Printf("[已发布] 主题: %s, 消息: %s\n", topic, payload)
	}
}

// Subscribe 订阅主题
func (m *MqttClient) Subscribe(topics []string, handler MessageHandler) {
	if !m.client.IsConnected() {
		fmt.Println("[错误] 客户端未连接")
		return
	}

	for _, topic := range topics {
		token := m.client.Subscribe(topic, m.config.Qos, func(c mqtt.Client, msg mqtt.Message) {
			payload := string(msg.Payload())
			fmt.Printf("[收到消息] 主题: %s, 消息: %s\n", msg.Topic(), payload)
			if handler != nil {
				handler(msg.Topic(), payload)
			}
		})
		token.Wait()

		if token.Error() != nil {
			fmt.Printf("[订阅失败] %v\n", token.Error())
		}
	}

	fmt.Printf("[已订阅] 主题: %v\n", topics)
}

// SubscribeSingle 订阅单个主题
func (m *MqttClient) SubscribeSingle(topic string, handler MessageHandler) {
	m.Subscribe([]string{topic}, handler)
}

// Unsubscribe 取消订阅
func (m *MqttClient) Unsubscribe(topics []string) {
	if !m.client.IsConnected() {
		fmt.Println("[错误] 客户端未连接")
		return
	}

	token := m.client.Unsubscribe(topics...)
	token.Wait()

	if token.Error() != nil {
		fmt.Printf("[取消订阅失败] %v\n", token.Error())
	} else {
		fmt.Printf("[已取消订阅] 主题: %v\n", topics)
	}
}

// Disconnect 断开连接
func (m *MqttClient) Disconnect() {
	if m.client.IsConnected() {
		m.client.Disconnect(250)
		fmt.Println("[已断开] 客户端已断开连接")
	}
}

// IsConnected 检查是否已连接
func (m *MqttClient) IsConnected() bool {
	return m.client.IsConnected()
}

// ============== 使用示例 ==============
func main() {
	mqttClient := NewMqttClient(config)

	// 连接
	mqttClient.Connect()

	// 等待连接建立
	time.Sleep(1 * time.Second)

	// 订阅主题
	mqttClient.SubscribeSingle(config.Topic, func(topic string, message string) {
		fmt.Printf("回调收到: %s -> %s\n", topic, message)
	})

	// 发布消息
	mqttClient.Publish(config.Topic, "Hello MQTT from Go!")
	mqttClient.Publish(config.Topic, map[string]string{
		"type": "json",
		"data": "test",
	})

	// 等待信号退出
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	// 10秒后自动断开
	go func() {
		time.Sleep(10 * time.Second)
		mqttClient.Disconnect()
		sigChan <- syscall.SIGTERM
	}()

	<-sigChan
	fmt.Println("程序退出")
}