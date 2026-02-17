/*
 * MQTT 客户端 - C#
 * 
 * NuGet 包安装: dotnet add package MQTTnet
 * 编译运行: dotnet run
 */

using System;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using MQTTnet;
using MQTTnet.Client;
using MQTTnet.Client.Options;

namespace MqttUtils
{
    /// <summary>
    /// MQTT 客户端配置
    /// </summary>
    public class MqttConfig
    {
        public string Broker { get; set; } = "localhost";
        public int Port { get; set; } = 1883;
        public string ClientId { get; set; } = $"mqtt_csharp_client_{Guid.NewGuid().ToString("N").Substring(0, 8)}";
        public string Username { get; set; } = "";
        public string Password { get; set; } = "";
        public string Topic { get; set; } = "test/topic";
        public int Qos { get; set; } = 1;
    }

    /// <summary>
    /// MQTT 客户端
    /// </summary>
    public class MqttClient : IDisposable
    {
        // ============== 配置区域 ==============
        private readonly MqttConfig _config;
        private IMqttClient _client;
        private bool _disposed;
        
        /// <summary>
        /// 消息接收事件
        /// </summary>
        public event Action<string, string> OnMessageReceived;
        // =====================================

        public MqttClient(MqttConfig config = null)
        {
            _config = config ?? new MqttConfig();
            var factory = new MqttFactory();
            _client = factory.CreateMqttClient();
            
            // 设置回调
            _client.UseConnectedHandler(e =>
            {
                Console.WriteLine($"[已连接] 连接到代理: {_config.Broker}:{_config.Port}");
            });
            
            _client.UseDisconnectedHandler(e =>
            {
                Console.WriteLine($"[已断开] 连接已关闭");
            });
            
            _client.UseApplicationMessageReceivedHandler(e =>
            {
                var topic = e.ApplicationMessage.Topic;
                var payload = Encoding.UTF8.GetString(e.ApplicationMessage.Payload);
                Console.WriteLine($"[收到消息] 主题: {topic}, 消息: {payload}");
                OnMessageReceived?.Invoke(topic, payload);
            });
        }

        /// <summary>
        /// 连接到 MQTT 代理
        /// </summary>
        public async Task<MqttClient> ConnectAsync()
        {
            var optionsBuilder = new MqttClientOptionsBuilder()
                .WithClientId(_config.ClientId)
                .WithTcpServer(_config.Broker, _config.Port)
                .WithCleanSession();

            if (!string.IsNullOrEmpty(_config.Username))
            {
                optionsBuilder.WithCredentials(_config.Username, _config.Password);
            }

            var options = optionsBuilder.Build();

            try
            {
                await _client.ConnectAsync(options, CancellationToken.None);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[连接错误] {ex.Message}");
            }

            return this;
        }

        /// <summary>
        /// 同步连接
        /// </summary>
        public MqttClient Connect()
        {
            return ConnectAsync().GetAwaiter().GetResult();
        }

        /// <summary>
        /// 发布消息
        /// </summary>
        /// <param name="topic">主题</param>
        /// <param name="message">消息内容</param>
        /// <param name="qos">服务质量等级 (0, 1, 2)</param>
        public async Task PublishAsync(string topic, object message, int qos = -1)
        {
            if (!_client.IsConnected)
            {
                Console.WriteLine("[错误] 客户端未连接");
                return;
            }

            if (qos < 0) qos = _config.Qos;

            string payload;
            if (message is string str)
            {
                payload = str;
            }
            else
            {
                payload = JsonSerializer.Serialize(message);
            }

            var mqttMessage = new MqttApplicationMessageBuilder()
                .WithTopic(topic)
                .WithPayload(payload)
                .WithAtMostOnceQoS() // qos 0
                .Build();

            if (qos == 1) mqttMessage = new MqttApplicationMessageBuilder()
                .WithTopic(topic)
                .WithPayload(payload)
                .WithAtLeastOnceQoS()
                .Build();
            else if (qos == 2) mqttMessage = new MqttApplicationMessageBuilder()
                .WithTopic(topic)
                .WithPayload(payload)
                .WithExactlyOnceQoS()
                .Build();

            try
            {
                await _client.PublishAsync(mqttMessage, CancellationToken.None);
                Console.WriteLine($"[已发布] 主题: {topic}, 消息: {payload}");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[发布失败] {ex.Message}");
            }
        }

        /// <summary>
        /// 同步发布
        /// </summary>
        public void Publish(string topic, object message, int qos = -1)
        {
            PublishAsync(topic, message, qos).GetAwaiter().GetResult();
        }

        /// <summary>
        /// 订阅主题
        /// </summary>
        /// <param name="topics">主题数组</param>
        public async Task SubscribeAsync(string[] topics)
        {
            if (!_client.IsConnected)
            {
                Console.WriteLine("[错误] 客户端未连接");
                return;
            }

            try
            {
                var builder = new MqttTopicFilterBuilder();
                
                foreach (var topic in topics)
                {
                    var filter = new MqttTopicFilterBuilder()
                        .WithTopic(topic)
                        .WithAtLeastOnceQoS()
                        .Build();
                    
                    await _client.SubscribeAsync(filter);
                }
                
                Console.WriteLine($"[已订阅] 主题: {string.Join(", ", topics)}");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[订阅失败] {ex.Message}");
            }
        }

        /// <summary>
        /// 订阅单个主题
        /// </summary>
        public async Task SubscribeAsync(string topic)
        {
            await SubscribeAsync(new[] { topic });
        }

        /// <summary>
        /// 同步订阅
        /// </summary>
        public void Subscribe(string topic)
        {
            SubscribeAsync(topic).GetAwaiter().GetResult();
        }

        /// <summary>
        /// 取消订阅
        /// </summary>
        public async Task UnsubscribeAsync(string[] topics)
        {
            if (!_client.IsConnected)
            {
                Console.WriteLine("[错误] 客户端未连接");
                return;
            }

            try
            {
                await _client.UnsubscribeAsync(topics);
                Console.WriteLine($"[已取消订阅] 主题: {string.Join(", ", topics)}");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[取消订阅失败] {ex.Message}");
            }
        }

        /// <summary>
        /// 断开连接
        /// </summary>
        public async Task DisconnectAsync()
        {
            if (_client.IsConnected)
            {
                await _client.DisconnectAsync();
                Console.WriteLine("[已断开] 客户端已断开连接");
            }
        }

        /// <summary>
        /// 检查是否已连接
        /// </summary>
        public bool IsConnected => _client.IsConnected;

        public void Dispose()
        {
            if (!_disposed)
            {
                DisconnectAsync().GetAwaiter().GetResult();
                _client?.Dispose();
                _disposed = true;
            }
        }
    }

    // ============== 使用示例 ==============
    class Program
    {
        static async Task Main(string[] args)
        {
            var config = new MqttConfig();
            using var mqttClient = new MqttClient(config);
            
            // 连接
            await mqttClient.ConnectAsync();
            
            // 等待连接建立
            await Task.Delay(1000);
            
            // 订阅主题
            mqttClient.OnMessageReceived += (topic, message) =>
            {
                Console.WriteLine($"回调收到: {topic} -> {message}");
            };
            await mqttClient.SubscribeAsync(config.Topic);
            
            // 发布消息
            await mqttClient.PublishAsync(config.Topic, "Hello MQTT from C#!");
            await mqttClient.PublishAsync(config.Topic, new { type = "json", data = "test" });
            
            // 保持运行
            await Task.Delay(10000);
            
            // 断开连接
            await mqttClient.DisconnectAsync();
        }
    }
}