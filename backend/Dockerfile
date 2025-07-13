# 使用本地已有的Python镜像
FROM 1python-api:latest

# 设置工作目录
WORKDIR /app

# 安装系统依赖（使用wget代替curl）
RUN apt-get update && apt-get install -y --no-install-recommends wget && rm -rf /var/lib/apt/lists/*

# 复制本地代码到容器中
COPY . /app

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 设置 Flask 环境变量
ENV FLASK_APP=app.py
ENV FLASK_ENV=development
ENV PYTHONPATH=/app

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8000/health || exit 1

# 开放端口
EXPOSE 8000

# 复制启动脚本
COPY entrypoint_simple.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# 启动 Flask 应用
CMD ["/app/entrypoint.sh"]
