# MQTT 客户端工具集

本目录包含多种编程语言的 MQTT 客户端实现，用于上传和接收数据。

---

## 版本信息

| 版本号 | 发布日期 | 说明 |
|--------|----------|------|
| v1.1.0 | 2026-02-18 | 新增 MQTT 客户端工具集 |

---

## 支持的语言

| 语言 | 文件 | 依赖库 |
|------|------|--------|
| JavaScript (Node.js) | `mqtt-client.js` | mqtt |
| Python | `mqtt_client.py` | paho-mqtt |
| Java | `MqttClient.java` | Eclipse Paho |
| C# | `MqttClient.cs` | MQTTnet |
| Go | `mqtt_client.go` | eclipse/paho.mqtt.golang |

---

## 快速开始

### JavaScript (Node.js)

```bash
npm install mqtt
node mqtt-client.js
```

### Python

```bash
pip install paho-mqtt
python mqtt_client.py
```

### Java

添加 Maven 依赖：
```xml
<dependency>
    <groupId>org.eclipse.paho</groupId>
    <artifactId>org.eclipse.paho.client.mqttv3</artifactId>
    <version>1.2.5</version>
</dependency>
```

### C#

```bash
dotnet add package MQTTnet
```

### Go

```bash
go get github.com/eclipse/paho.mqtt.golang
```

---

## 配置说明

所有客户端默认连接配置：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| BROKER | tcp://localhost:1883 | MQTT 代理地址 |
| CLIENT_ID | auto-generated | 客户端 ID |
| TOPIC | test/topic | 默认主题 |
| QOS | 1 | 服务质量等级 |

---

## API 说明

每个客户端提供以下核心功能：

1. **连接** - 连接到 MQTT 代理
2. **发布** - 发布消息到指定主题
3. **订阅** - 订阅主题并接收消息
4. **断开** - 断开与代理的连接