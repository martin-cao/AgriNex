from flask import Flask
from flask_cors import CORS
from extensions import db, jwt
from config import Config
import pymysql
from dotenv import load_dotenv
import os

# 安装 PyMySQL 作为 MySQLdb
pymysql.install_as_MySQLdb()
load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # 检查是否为开发模式（允许无数据库启动）
    dev_mode = os.getenv('FLASK_ENV') == 'development' and os.getenv('ALLOW_NO_DB', '').lower() == 'true'
    
    # 初始化扩展
    db.init_app(app)
    jwt.init_app(app)
    CORS(app)
    
    # 初始化Redis（优雅降级）
    redis_available = False
    try:
        from utils.redis_client import redis_client
        redis_client.init_app(app)
        redis_available = hasattr(redis_client, 'client') and redis_client.client is not None
        if redis_available:
            app.logger.info("Redis initialized successfully")
        else:
            app.logger.warning("Redis connection failed, using fallback")
    except Exception as e:
        app.logger.warning(f"Redis initialization failed: {e}")
    
    # 注册蓝图
    from controllers.device_controller import device_bp
    from controllers.auth_controller import auth_bp
    from controllers.mcp_controller import mcp_bp
    
    app.register_blueprint(device_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(mcp_bp, url_prefix='/api/mcp')
    
    # 基本路由
    @app.route('/')
    def hello():
        return {"message": "AgriNex API is running!", "mode": "development" if dev_mode else "production"}
    
    @app.route('/api/health')
    def health():
        # 检查服务状态
        mysql_status = "unknown"
        redis_status = "available" if redis_available else "fallback"
        
        try:
            with app.app_context():
                db.session.execute('SELECT 1')
            mysql_status = "connected"
        except Exception:
            mysql_status = "disconnected"
        
        return {
            "status": "healthy",
            "services": {
                "mysql": mysql_status,
                "redis": redis_status
            },
            "dev_mode": dev_mode
        }
    
    # 创建数据库表（如果可能）
    if not dev_mode:
        # 生产模式，必须有数据库
        with app.app_context():
            try:
                db.create_all()
                app.logger.info("Database tables created successfully")
            except Exception as e:
                app.logger.error(f"Database initialization failed: {e}")
                raise
    else:
        # 开发模式，数据库可选
        with app.app_context():
            try:
                db.create_all()
                app.logger.info("Database tables created successfully")
            except Exception as e:
                app.logger.warning(f"Database not available in dev mode: {e}")
                app.logger.info("Running in database-free mode - some features may be limited")
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
