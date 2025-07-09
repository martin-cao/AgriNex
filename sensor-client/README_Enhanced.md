# 增强的MQTT传感器系统

## 系统概述

这是一个支持多类型传感器设备的MQTT客户端和服务端系统，能够模拟各种传感器设备通过串口（包括虚拟串口）传输数据，支持数值、图片、视频等多种数据类型，并通过MQTT协议发送到后端进行处理和存储。

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    增强的MQTT传感器系统                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐ │
│  │  虚拟串口模拟器   │    │   MQTT客户端     │    │   MQTT代理      │ │
│  │                 │    │                 │    │                 │ │
│  │ • 智慧农场设备   │<-->│ • 数据采集       │<-->│ • 消息转发       │ │
│  │ • 气象站设备     │    │ • 格式转换       │    │ • 主题管理       │ │
│  │ • 环境监测设备   │    │ • 图像处理       │    │ • 负载均衡       │ │
│  │ • 水管理设备     │    │ • 错误处理       │    │                 │ │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘ │
│           │                       │                       │        │
│           v                       v                       v        │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐ │
│  │  多种数据格式    │    │   数据处理       │    │   后端服务       │ │
│  │                 │    │                 │    │                 │ │
│  │ • JSON          │    │ • 数据解析       │    │ • 数据存储       │ │
│  │ • CSV           │    │ • 质量检测       │    │ • API接口        │ │
│  │ • 二进制         │    │ • 异常处理       │    │ • 报警系统       │ │
│  │ • 自定义格式     │    │ • 统计分析       │    │ • 数据可视化     │ │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 主要特性

### 1. 增强的虚拟串口模拟器
- **多种传感器类型**: 支持温度、湿度、光照、土壤、气象、环境监测等
- **多种数据格式**: JSON、CSV、二进制、自定义格式
- **智能设备模拟**: 模拟真实传感器的数据变化规律
- **设备状态监控**: 电池电量、信号强度、错误统计等
- **可配置参数**: 发送间隔、数据精度、错误率等

### 2. 增强的MQTT客户端
- **多格式数据处理**: 自动检测和处理不同数据格式
- **智能串口扫描**: 自动发现和连接虚拟串口
- **图像视频支持**: 支持摄像头捕获和模拟数据
- **远程控制**: 支持MQTT控制命令
- **错误恢复**: 自动重连和错误处理

### 3. 系统集成测试
- **多客户端并发**: 支持多个客户端同时运行
- **自动化测试**: 完整的系统集成测试框架
- **性能统计**: 实时监控消息吞吐量和错误率
- **测试报告**: 自动生成详细的测试报告

## 文件结构

```
sensor-client/
├── enhanced_serial_simulator.py    # 增强的串口设备模拟器
├── enhanced_mqtt_client.py         # 增强的MQTT客户端
├── enhanced_simple_demo.py         # 简化演示脚本
├── enhanced_system_test.py         # 系统测试脚本
├── enhanced_start_system.py        # 一键启动脚本
├── README_Enhanced.md              # 详细说明文档
└── requirements.txt                # 依赖项列表
```

## 快速开始

### 1. 环境准备

```bash
# 安装Python依赖
pip install paho-mqtt numpy opencv-python pyserial

# 安装MQTT代理 (可选，用于完整演示)
# macOS:
brew install mosquitto

# Ubuntu:
sudo apt-get install mosquitto

# 或使用Docker:
docker run -it -p 1883:1883 eclipse-mosquitto
```

### 2. 快速演示

```bash
# 方式1: 使用一键启动脚本
python enhanced_start_system.py demo --duration 60

# 方式2: 直接运行简化演示
python enhanced_simple_demo.py --duration 60

# 方式3: 只运行串口模拟器
python enhanced_serial_simulator.py --interval 5.0
```

### 3. 完整MQTT系统演示

```bash
# 终端1: 启动MQTT代理
mosquitto -p 1883 -v

# 终端2: 启动MQTT客户端
python enhanced_mqtt_client.py --client-id demo_client

# 或使用一键启动脚本
python enhanced_start_system.py full --duration 120
```

### 4. 系统测试

```bash
# 运行完整系统测试
python enhanced_system_test.py --duration 300 --clients 3

# 或使用一键启动脚本
python enhanced_start_system.py test --duration 300 --clients 3
```

## 详细使用指南

### 1. 串口模拟器

#### 基本用法

```bash
# 启动默认配置
python enhanced_serial_simulator.py

# 自定义配置
python enhanced_serial_simulator.py --interval 10.0 --format json
```

#### 支持的传感器类型

- **智慧农场设备**: 温度、湿度、光照、土壤湿度、土壤pH、土壤EC
- **气象站设备**: 温度、湿度、气压、风速、风向、降雨量、紫外线指数
- **环境监测设备**: 温度、湿度、CO2、噪声、光照
- **水管理设备**: 水位、流速、压力、温度

#### 数据格式示例

**JSON格式**:
```json
{
  "device_id": "FARM_001",
  "timestamp": "2024-01-15T10:30:00",
  "readings": [
    {
      "sensor_id": "temp_01",
      "sensor_type": "temperature",
      "value": 25.5,
      "unit": "°C",
      "quality": 1.0
    }
  ],
  "device_status": {
    "battery_level": 85.0,
    "signal_strength": 95.0
  }
}
```

**CSV格式**:
```
FARM_001,2024-01-15 10:30:00,temp_01,temperature,25.5,°C,1.0
FARM_001,2024-01-15 10:30:00,hum_01,humidity,60.2,%,1.0
```

**自定义格式**:
```
FARM_001:temperature:25.5:°C;FARM_001:humidity:60.2:%;
```

### 2. MQTT客户端

#### 基本用法

```bash
# 启动客户端
python enhanced_mqtt_client.py --client-id sensor_001

# 自定义配置
python enhanced_mqtt_client.py \
  --client-id sensor_001 \
  --mqtt-host localhost \
  --mqtt-port 1883 \
  --scan-interval 10.0 \
  --camera
```

#### MQTT主题结构

- **传感器数据**: `sensors/{client_id}/{port}/`
- **图像数据**: `sensors/{client_id}/camera/image`
- **视频数据**: `sensors/{client_id}/camera/video`
- **状态信息**: `status/{client_id}`
- **控制命令**: `control/{client_id}/{command}`
- **响应消息**: `response/{client_id}/{command}`

#### 控制命令

**配置更新**:
```bash
# 主题: control/{client_id}/config
{
  "scan_interval": 30.0,
  "image_interval": 60.0,
  "camera_enabled": true
}
```

**数据捕获**:
```bash
# 主题: control/{client_id}/capture
{
  "type": "image"  # 或 "video", "snapshot"
}
```

**状态查询**:
```bash
# 主题: control/{client_id}/status
{}
```

### 3. 系统测试

#### 测试配置

```bash
# 基本测试
python enhanced_system_test.py

# 自定义测试
python enhanced_system_test.py \
  --duration 600 \
  --clients 5 \
  --mqtt-port 1883
```

#### 测试指标

- **消息吞吐量**: 每秒处理的消息数
- **错误率**: 失败消息的百分比
- **响应时间**: 消息端到端延迟
- **资源使用**: CPU和内存使用率
- **连接稳定性**: 连接断开和重连次数

#### 测试报告

测试完成后会生成详细的JSON报告：

```json
{
  "test_info": {
    "start_time": "2024-01-15T10:00:00",
    "duration": 300,
    "client_count": 3
  },
  "statistics": {
    "total_messages": 1500,
    "error_count": 5,
    "success_rate": 99.67
  },
  "clients": [...],
  "devices": {...}
}
```

## 系统监控

### 1. 实时监控

```bash
# 启动监控脚本
python enhanced_simple_demo.py --duration 3600 --verbose
```

### 2. 日志分析

系统会生成详细的日志文件：
- `mqtt_system_test.log`: 系统测试日志
- `demo_data_*.json`: 演示数据文件

### 3. 性能指标

- **设备状态**: 电池电量、信号强度、运行时间
- **数据质量**: 数据完整性、时间戳准确性
- **网络性能**: 连接稳定性、消息延迟
- **系统资源**: CPU使用率、内存占用

## 高级功能

### 1. 自定义传感器设备

```python
from enhanced_serial_simulator import BaseEnhancedSensorDevice, SensorType

class CustomSensorDevice(BaseEnhancedSensorDevice):
    def __init__(self, device_id, serial_port):
        super().__init__(device_id, serial_port)
        
        # 添加自定义传感器
        self.add_sensor('custom_01', SensorType.TEMPERATURE, 
                       (0.0, 100.0), '°C', change_rate=1.0)
```

### 2. 自定义数据格式

```python
def _format_custom(self, readings):
    """自定义数据格式"""
    # 实现自定义格式逻辑
    return formatted_data.encode('utf-8')
```

### 3. 扩展MQTT客户端

```python
class CustomMQTTClient(EnhancedMQTTSensorClient):
    def __init__(self, client_id, mqtt_config):
        super().__init__(client_id, mqtt_config)
        
    def custom_data_handler(self, data):
        """自定义数据处理"""
        # 实现自定义处理逻辑
        pass
```

## 故障排除

### 1. 常见问题

**Q: MQTT代理连接失败**
```
A: 检查mosquitto是否已安装和启动
   brew install mosquitto
   mosquitto -p 1883 -v
```

**Q: 虚拟串口无数据**
```
A: 确保设备模拟器已启动
   python enhanced_serial_simulator.py
```

**Q: 摄像头初始化失败**
```
A: 检查opencv-python是否已安装
   pip install opencv-python
```

### 2. 调试模式

```bash
# 启用详细日志
python enhanced_mqtt_client.py --verbose

# 检查系统状态
python enhanced_start_system.py check
```

### 3. 性能优化

- **减少扫描间隔**: 降低CPU使用率
- **调整数据格式**: 使用二进制格式减少带宽
- **优化传感器数量**: 根据需要添加传感器
- **使用连接池**: 复用MQTT连接

## 扩展开发

### 1. 添加新的传感器类型

```python
# 在enhanced_serial_simulator.py中添加
class NewSensorType(Enum):
    CUSTOM_SENSOR = "custom_sensor"

# 创建对应的设备类
class CustomDevice(BaseEnhancedSensorDevice):
    # 实现设备逻辑
```

### 2. 集成其他协议

```python
# 添加新的通信协议支持
class ModbusConnector:
    def __init__(self):
        # 实现Modbus协议
        pass
```

### 3. 数据库集成

```python
# 添加数据库存储
class DatabaseHandler:
    def store_sensor_data(self, data):
        # 存储到数据库
        pass
```

## 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 联系方式

如有问题或建议，请通过以下方式联系：
- 邮箱: your.email@example.com
- GitHub Issues: https://github.com/your-repo/issues

---

**注意**: 这是一个模拟系统，主要用于开发和测试。在生产环境中使用时，请确保进行充分的测试和安全评估。
