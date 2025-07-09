# 使用 Python 3.9 的基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制本地代码到容器中
COPY . /app

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 设置 Flask 环境变量
ENV FLASK_APP=app.py
ENV FLASK_ENV=development
ENV PYTHONPATH=/app

# 开放端口
EXPOSE 8000

# 启动 Flask 应用
CMD ["python", "app.py"]
