# AgriNex - 农业物联网数据管理平台

基于 Flask + Vue.js + MCP 的农业物联网数据采集与可视化平台

## 快速开始

### 后端 (Flask)
```bash
cd backend
pip install -r requirements.txt
python app.py
```
访问：http://localhost:8000

### MCP Server (Flask)
```bash
cd mcp-server
pip install -r requirements.txt
python app.py
```
访问：http://localhost:8001

### 前端 (Vue.js)
```bash
cd frontend
npm install
npm run dev
```
访问：http://localhost:5173

## 项目结构
```
AgriNex/
├── backend/           # Flask 后端
│   ├── models/        # 数据模型
│   ├── controllers/   # 路由控制器
│   └── services/      # 业务逻辑
├── mcp-server/        # MCP 自然语言控制服务
│   ├── handlers/      # 意图处理器
│   ├── tools/         # 功能工具
│   └── utils/         # 工具函数
├── frontend/          # Vue.js 前端
│   └── src/
│       ├── components/
│       └── views/
└── sensor-client/     # 传感器模拟器
```