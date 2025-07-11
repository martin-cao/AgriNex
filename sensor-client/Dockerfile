# Sensor Client Dockerfile
FROM python:3.9-slim

# 安装系统依赖，包括 OpenGL 和 OpenCV 所需的库
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制requirements文件
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制源代码
COPY . .

# 设置环境变量
ENV PYTHONPATH=/app

# 启动传感器模拟器
CMD ["python", "enhanced_mqtt_client.py"]
