# AgriNex - 农业物联网数据管理平台

基于 Flask + Vue.js + MCP 的农业物联网数据采集与可视化平台，支持传感器数据收集、实时监控、智能告警和数据分析。

主要特性：
- 📡 统一的传感器数据采集与存储
- 🤖 基于 GPT 的 AI 分析与智能建议
- 🛰 实时监控与灵活告警规则
- 🌐 前后端分离的 Web 界面和 API

## 🚀 快速启动

### 方式一：Docker 容器启动（推荐）

**1. 启动完整系统**
```bash
# 启动所有服务（MySQL、Redis、MQTT、MinIO、Backend）
docker-compose up -d

# 查看服务状态
docker-compose ps
```

**2. 启动开发模式**
```bash
# 使用 fish shell 脚本
./start_dev.fish

# 或者手动启动
./start_complete_system.sh
```

**3. 访问服务**
- 后端API: http://localhost/api
- 前端界面: http://localhost
- MinIO对象存储: http://localhost:9001
- MQTT服务: localhost:1883
- Redis: localhost:6379
- MySQL: localhost:3307

## 🌱 模拟设备管理

AgriNex 支持通过脚本快速添加虚拟设备进行测试和演示。

### 添加模拟设备

使用 `scripts/start_simulator_device.sh` 脚本可以快速启动虚拟设备容器：

```bash
# 基本用法 - 启动土壤传感器
./scripts/start_simulator_device.sh --device-id SIM_001 --type soil_sensor

# 启动气象站
./scripts/start_simulator_device.sh --device-id SIM_002 --type weather_station

# 启动灌溉控制器并自定义参数
./scripts/start_simulator_device.sh \
  --device-id SIM_003 \
  --type irrigation_controller \
  --port 30003 \
  --interval 15
```

### 支持的设备类型

- **soil_sensor**: 土壤传感器 - 监测土壤湿度、温度、pH值
- **weather_station**: 气象站 - 监测气温、湿度、气压、风速
- **irrigation_controller**: 灌溉控制器 - 控制水泵、阀门状态

### 脚本参数说明

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--device-id` | `-i` | 设备唯一ID（必需） | - |
| `--type` | `-t` | 设备类型 | `soil_sensor` |
| `--port` | `-p` | HTTP端口号 | 自动分配（从30001开始） |
| `--mqtt-host` | `-m` | MQTT主机地址 | `mosquitto` |
| `--interval` | `-n` | 数据发送间隔（秒） | `30` |
| `--help` | `-h` | 显示帮助信息 | - |

### 设备容器管理

AgriNex 的 `scripts/start_simulator_device.sh` 脚本现在集成了完整的设备管理功能：

**查看和状态管理：**
```bash
# 查看所有设备状态
./scripts/start_simulator_device.sh list

# 查看系统状态（包括端口使用情况）
./scripts/start_simulator_device.sh status

# 查看设备日志
./scripts/start_simulator_device.sh logs SIM_001

# 检查设备健康状态
./scripts/start_simulator_device.sh health SIM_001
```

**设备生命周期管理：**
```bash
# 停止指定设备
./scripts/start_simulator_device.sh stop SIM_001

# 启动已存在的设备
./scripts/start_simulator_device.sh start SIM_001

# 删除设备容器
./scripts/start_simulator_device.sh remove SIM_001

# 停止所有设备
./scripts/start_simulator_device.sh stop-all

# 清理所有停止的容器
./scripts/start_simulator_device.sh clean
```

**手动管理命令（备用）：**
```bash
# 查看运行的设备容器
docker ps | grep sensor-sim

# 查看设备日志
docker logs sensor-sim-SIM_001

# 停止设备
docker stop sensor-sim-SIM_001

# 删除设备容器
docker rm -f sensor-sim-SIM_001

# 测试设备健康状态
curl http://localhost:30001/health
```

### 在前端添加设备

1. 启动模拟设备容器后，访问 AgriNex 前端界面
2. 进入"设备管理"页面
3. 点击"添加设备"
4. 填写设备信息：
   - **设备ID**: 与脚本中的 `--device-id` 一致
   - **设备名称**: 自定义名称
   - **设备类型**: 选择对应类型
   - **设备地址**: `localhost:端口号`（如：`localhost:30001`）
5. 保存后设备将开始发送模拟数据

### 批量设备启动示例

```bash
# 启动一套完整的农场模拟环境
./scripts/start_simulator_device.sh -i FARM_SOIL_01 -t soil_sensor -p 30001
./scripts/start_simulator_device.sh -i FARM_WEATHER_01 -t weather_station -p 30002
./scripts/start_simulator_device.sh -i FARM_IRRIGATION_01 -t irrigation_controller -p 30003

# 启动多个土壤传感器
for i in {1..5}; do
  ./scripts/start_simulator_device.sh -i "SOIL_$(printf %02d $i)" -t soil_sensor
done
```

### 注意事项

- 确保 AgriNex 主系统已启动（`docker-compose up -d`）
- 设备ID必须唯一，重复的ID会导致启动失败
- 端口号会自动分配，避免冲突
- 设备容器使用与主系统相同的Docker网络
- 停止主系统前建议先清理所有设备容器

### 方式二：本地开发启动

**1. 启动依赖服务**
```bash
# 启动数据库、缓存、消息队列等基础服务
docker-compose up -d mysql redis mosquitto minio
```

**2. 启动后端服务**
```bash
cd backend
pip install -r requirements.txt
python app.py
```

**3. 启动前端服务**
```bash
cd frontend
npm install
npm run dev
```

**4. 添加模拟设备（可选）**
```bash
# 启动虚拟设备进行测试
./scripts/start_simulator_device.sh --device-id TEST_001 --type soil_sensor
```

## 📋 系统要求

- Python 3.9+
- Node.js 16+
- Docker & Docker Compose
- MySQL 8.0+
- Redis 7+
- MQTT Broker (Eclipse Mosquitto)

## 🏗️ 项目架构

```
AgriNex/
├── backend/                    # Flask后端服务
│   ├── controllers/           # API控制器
│   ├── models/               # 数据模型
│   ├── services/             # 业务逻辑
│   ├── utils/                # 工具类
│   ├── app.py               # 应用入口
│   └── requirements.txt     # Python依赖
├── frontend/                  # Vue.js前端
│   ├── src/
│   │   ├── components/      # 组件
│   │   └── views/           # 页面
│   ├── package.json
│   └── vite.config.ts
├── mcp-server/               # MCP智能助手
│   ├── handlers/            # 消息处理器
│   ├── tools/               # 工具函数
│   └── main.py
├── sensor-client/            # 传感器模拟器
│   ├── main.py              # 模拟器主程序
│   └── requirements.txt
├── scripts/                  # 工具脚本
│   └── start_simulator_device.sh  # 设备启动脚本
├── db/                       # 数据库脚本
│   └── init_db.sql
├── docs/                     # 项目文档
├── storage/                  # 文件存储
└── docker-compose.yml        # 容器编排
```

## 🔧 核心功能

### 1. 设备与传感器管理
- 设备注册与管理
- 传感器配置与监控
- 设备状态实时追踪

### 2. 数据采集与存储
- 支持数值、图像、视频数据
- MQTT消息队列处理
- MinIO对象存储
- MySQL关系型数据库

### 3. 实时监控与告警
- 自定义告警规则
- 实时数据监控
- 多种通知方式（邮件、Webhook）
- 告警历史记录

### 4. 数据分析与预测
- 历史数据分析
- 趋势预测
- 智能建议系统

## 🔔 告警系统

### 创建告警规则
```python
# 示例：温度超过30度告警
rule = {
    "name": "高温告警",
    "sensor_id": 1,
    "condition": ">",
    "threshold_value": 30.0,
    "severity": "high"
}
```

### 告警类型
- **阈值告警**: 数值超过设定阈值
- **变化率告警**: 数值变化速率异常
- **模式告警**: 基于历史数据的异常模式

## 🧪 测试

### 运行系统测试
```bash
# 测试告警系统
python test_alarm_system.py

# 测试MQTT通信
python test_mqtt_communication.py

# 测试传感器数据流
python test_sensor_data_flow.py
```

### 健康检查
```bash
# 检查服务状态
curl http://localhost/api/health

# 检查数据库连接
curl http://localhost/api/status
```

## 🛠️ 开发指南

### 环境配置
```bash
# 复制环境配置文件
cp .env.example .env

# 编辑配置（数据库、Redis、MQTT等）
vim .env
```

### 数据库迁移
```bash
# 初始化数据库
docker-compose exec mysql mysql -u root -p agrinex < db/init_db.sql

# 或使用迁移脚本
python backend/migrate_alarm_tables.py
```

### 代码规范
- 使用 Black 格式化 Python 代码
- 使用 ESLint 格式化 JavaScript/TypeScript 代码
- 遵循 RESTful API 设计原则

## 📊 监控与日志

### 查看服务日志
```bash
# 查看后端日志
docker-compose logs backend

# 查看所有服务日志
docker-compose logs -f
```

### 性能监控
- 系统资源使用情况
- API响应时间
- 数据库查询性能
- MQTT消息处理速度

## 🔒 安全

### 认证与授权
- JWT令牌认证
- 用户权限管理
- API访问控制

### 数据安全
- 数据库连接加密
- 敏感信息环境变量管理
- 文件上传安全检查

## 🚀 部署

### 生产环境部署
```bash
# 构建生产镜像
docker-compose -f docker-compose.prod.yml build

# 启动生产服务
docker-compose -f docker-compose.prod.yml up -d
```

### 环境变量
```bash
# 生产环境必需配置
FLASK_ENV=production
MYSQL_HOST=your-db-host
REDIS_HOST=your-redis-host
MQTT_BROKER=your-mqtt-broker
MINIO_ENDPOINT=your-minio-endpoint
```

## 📝 API 文档

API文档可通过以下方式查看：
- Swagger UI: http://localhost:8000/api/docs
- OpenAPI规范: [openapi.yaml](openapi.yaml)

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交修改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

---

**最后更新**: 2025-07-19