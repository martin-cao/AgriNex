# MQTT 传感器客户端和服务端系统

## 系统概述

本系统实现了一个完整的MQTT传感器数据采集和传输解决方案，支持：
- 数值型传感器数据（温度、湿度、光照）
- 图像数据传输
- 视频数据传输
- 串口通信
- 网络传输
- 多种数据格式和编码

## 架构设计

```
┌─────────────────┐    MQTT     ┌─────────────────┐    API     ┌─────────────────┐
│  传感器客户端    │ ─────────► │   MQTT Broker   │ ─────────► │     后端服务     │
│                │            │   (Mosquitto)   │            │    (Flask)      │
│ • 数值传感器     │            │                │            │                │
│ • 图像捕获      │            │ Topics:         │            │ • 数据摄取      │
│ • 视频录制      │            │ - sensors/+/    │            │ • 文件存储      │
│ • 串口通信      │            │ - control/+/    │            │ • 数据库存储    │
└─────────────────┘            └─────────────────┘            └─────────────────┘
```

## 主要组件

### 1. 传感器客户端 (`sensor-client/`)

#### 文件结构
```
sensor-client/
├── publisher.py        # 主要的传感器发布客户端
├── video_client.py     # 视频捕获客户端
├── config.py          # 配置管理
├── requirements.txt   # Python依赖
└── README.md         # 使用说明
```

#### 主要功能
- **数值传感器支持**：温度、湿度、光照传感器
- **串口通信**：自动检测和连接串口设备
- **图像捕获**：支持USB摄像头和网络摄像头
- **视频录制**：支持短视频录制和传输
- **数据编码**：Base64编码，支持多种格式
- **异步处理**：非阻塞数据采集和传输

#### 使用方法

1. **安装依赖**：
```bash
cd sensor-client
pip install -r requirements.txt
```

2. **配置环境变量**：
```bash
export SENSOR_CLIENT_ID="sensor_001"
export MQTT_HOST="localhost"
export MQTT_PORT="1883"
export SERIAL_PORT="/dev/ttyUSB0"  # 可选，自动检测
export CAMERA_DEVICE_ID="0"        # 默认摄像头
```

3. **运行传感器客户端**：
```bash
python publisher.py
```

4. **运行视频客户端**：
```bash
python video_client.py
```

### 2. 后端服务 (`backend/`)

#### 新增组件
- `services/mqtt_service.py` - MQTT服务管理
- `services/ingestion_service.py` - 数据摄取服务（已更新）
- `controllers/mqtt_controller.py` - MQTT API控制器

#### 数据流程
1. MQTT服务订阅传感器主题
2. 接收到消息后解析数据类型
3. 调用摄取服务处理数据
4. 存储到数据库和对象存储
5. 提供API接口查询数据

## MQTT 主题设计

### 数据主题 (传感器 → 后端)
```
sensors/{client_id}/numeric    # 数值数据
sensors/{client_id}/image      # 图像数据
sensors/{client_id}/video      # 视频数据
```

### 控制主题 (后端 → 传感器)
```
control/{client_id}/config     # 配置更新
control/{client_id}/capture    # 触发捕获
```

## 数据格式

### 数值数据格式
```json
{
  "type": "numeric",
  "data": {
    "temperature": 25.5,
    "temperature_unit": "°C",
    "humidity": 60.2,
    "humidity_unit": "%",
    "light": 1200.0,
    "light_unit": "lux"
  },
  "timestamp": "2024-01-01T10:00:00Z",
  "client_id": "sensor_001"
}
```

### 图像数据格式
```json
{
  "type": "image",
  "data": {
    "data": "base64_encoded_image_data",
    "format": "jpg",
    "size": 12345,
    "hash": "md5_hash",
    "encoding": "base64"
  },
  "timestamp": "2024-01-01T10:00:00Z",
  "client_id": "sensor_001"
}
```

### 视频数据格式
```json
{
  "type": "video",
  "data": {
    "data": "base64_encoded_video_data",
    "format": "avi",
    "size": 123456,
    "hash": "md5_hash",
    "encoding": "base64",
    "duration": 5,
    "fps": 20,
    "resolution": "640x480"
  },
  "timestamp": "2024-01-01T10:00:00Z",
  "client_id": "sensor_001"
}
```

## 串口通信协议

### 数值数据格式
传感器通过串口发送的数据格式：
```
T:25.5,H:60.2,L:1200.0\n
```

说明：
- `T:` - 温度值（摄氏度）
- `H:` - 湿度值（百分比）
- `L:` - 光照值（勒克斯）
- `,` - 字段分隔符
- `\n` - 消息结束符

### 串口配置
- 波特率：9600 (可配置)
- 数据位：8
- 停止位：1
- 校验位：None

## API接口

### MQTT控制接口

#### 获取MQTT状态
```
GET /api/mqtt/status
```

#### 发送传感器配置
```
POST /api/mqtt/sensors/{client_id}/config
Content-Type: application/json

{
  "numeric_interval": 5.0,
  "image_interval": 30.0
}
```

#### 触发数据捕获
```
POST /api/mqtt/sensors/{client_id}/capture
Content-Type: application/json

{
  "type": "image"  # 或 "video"
}
```

#### 发布MQTT消息
```
POST /api/mqtt/publish
Content-Type: application/json

{
  "topic": "control/sensor_001/config",
  "payload": {"interval": 5},
  "qos": 1
}
```

## 部署说明

### 1. MQTT Broker部署
使用Docker部署Mosquitto：
```bash
docker run -it -p 1883:1883 eclipse-mosquitto:2
```

### 2. 后端服务部署
```bash
cd backend
pip install -r requirements.txt
python app.py
```

### 3. 传感器客户端部署
```bash
cd sensor-client
pip install -r requirements.txt
python publisher.py
```

## 扩展功能

### 1. 数据压缩
- 对大型图像/视频数据进行压缩
- 支持多种压缩算法

### 2. 数据分片
- 大文件分片传输
- 支持断点续传

### 3. 加密传输
- TLS/SSL加密
- 数据端到端加密

### 4. 设备管理
- 设备注册和认证
- 设备状态监控
- 远程设备控制

## 故障处理

### 常见问题

1. **串口连接失败**
   - 检查串口设备是否存在
   - 确认串口权限
   - 检查波特率配置

2. **摄像头打开失败**
   - 检查摄像头设备ID
   - 确认摄像头权限
   - 检查其他程序是否占用

3. **MQTT连接失败**
   - 检查MQTT Broker是否运行
   - 确认网络连接
   - 检查认证信息

4. **数据传输失败**
   - 检查数据格式是否正确
   - 确认网络稳定性
   - 检查存储空间

### 日志查看
```bash
tail -f /var/log/agrinex/sensor-client.log
tail -f /var/log/agrinex/backend.log
```

## 性能优化

### 1. 传输优化
- 图像压缩质量调整
- 视频编码参数优化
- 数据批量传输

### 2. 存储优化
- 对象存储分层
- 数据生命周期管理
- 缓存机制

### 3. 并发处理
- 异步数据处理
- 多线程传输
- 队列管理

## 安全考虑

1. **认证授权**
   - MQTT用户名密码认证
   - JWT Token验证
   - 设备证书认证

2. **数据加密**
   - 传输层加密（TLS）
   - 应用层加密（AES）
   - 数据签名验证

3. **访问控制**
   - 主题权限控制
   - API访问限制
   - 设备隔离

## 监控和告警

1. **系统监控**
   - 连接状态监控
   - 数据传输量监控
   - 设备在线状态

2. **告警机制**
   - 连接断开告警
   - 数据异常告警
   - 设备离线告警

3. **性能指标**
   - 消息吞吐量
   - 传输延迟
   - 存储使用率
