# AgriNex 传感器客户端 - 统一启动接口

## 概述

AgriNex 传感器客户端提供了一个统一的启动接口，用于连接和管理农业IoT传感器。支持多种传感器类型，通过MQTT协议与后端服务器通信。

## 功能特性

- 🔌 **多种传感器支持**: 数值型、图像、视频传感器
- 📡 **MQTT通信**: 实时数据传输和远程控制
- 🔄 **自动重连**: 网络断开后自动重新连接
- 📊 **数据格式支持**: JSON、CSV、二进制、自定义格式
- 📸 **图像采集**: 支持摄像头和图像传感器
- 🖥️ **实时监控**: 客户端状态和数据流监控
- ⚙️ **配置管理**: 灵活的配置文件和命令行参数

## 文件结构

```
sensor-client/
├── sensor_launcher.py          # 主启动器（完整功能）
├── quick_start.py              # 快速启动脚本
├── monitor.py                  # 状态监控脚本
├── enhanced_mqtt_client.py     # MQTT客户端实现
├── enhanced_serial_simulator.py # 串口设备模拟器
├── client_config.json          # 配置文件
├── sensor_client.log           # 日志文件
└── README_NEW.md               # 新文档
```

## 启动接口

### 1. 主启动器 (sensor_launcher.py)

```bash
# 基本启动
python sensor_launcher.py

# 启用摄像头
python sensor_launcher.py --camera

# 自定义配置
python sensor_launcher.py --client-id my_sensor --mqtt-host 192.168.1.100

# 启用调试模式
python sensor_launcher.py --debug

# 创建配置文件
python sensor_launcher.py --create-config
```

### 2. 快速启动 (quick_start.py)

```bash
# 最简单的启动方式
python quick_start.py
```

### 3. 状态监控 (monitor.py)

```bash
# 启动监控器
python monitor.py
```

## 测试启动

让我们测试一下新的启动接口：

```bash
# 确保MQTT服务器正在运行
ps aux | grep mosquitto

# 快速启动传感器客户端
cd /Users/martincao/Developer/course-lab/comprehensive-programming/src/AgriNex/sensor-client
python quick_start.py
```

现在sensor-client已经有了统一的启动接口，提供了：

1. **完整功能的启动器** (`sensor_launcher.py`) - 支持配置文件和命令行参数
2. **快速启动脚本** (`quick_start.py`) - 简单的一键启动
3. **状态监控工具** (`monitor.py`) - 实时监控客户端状态
4. **配置管理** - 灵活的配置文件支持

所有脚本都已经整理完成，可以直接使用！
