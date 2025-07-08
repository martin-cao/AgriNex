# backend/app.py
"""
AgriNex - 农业物联网数据管理平台
统一版本，支持三层架构（Device-Sensor-Reading）和对象存储
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app(config_name='Config'):
    """应用工厂函数"""
    app = Flask(__name__)
    
    # 配置CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:3000", "http://localhost:8080"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # 配置应用
    from backend.config import Config
    app.config.from_object(Config)
    logger.info("Configuration loaded successfully")
    
    # 初始化扩展
    from backend.extensions import init_extensions
    init_extensions(app)
    logger.info("Extensions initialized successfully")
    
    # 注册蓝图
    register_blueprints(app)
    
    # 创建数据库表
    with app.app_context():
        # 初始化数据库，连接失败时直接抛出异常
        init_database(app)
        logger.info("Database initialization completed")
    
    # 注册错误处理器
    register_error_handlers(app)
    
    # 注册钩子函数
    register_hooks(app)
    
    return app

def register_blueprints(app):
    """注册蓝图"""
    # 主要路由
    from backend.controllers.main_controller import main_bp
    app.register_blueprint(main_bp, url_prefix='/api')
    logger.info("Registered main blueprint")

    # 设备管理API
    from backend.controllers.device_controller import device_bp
    app.register_blueprint(device_bp, url_prefix='/api/devices')
    logger.info("Registered device blueprint")

    # 传感器API
    from backend.controllers.sensor_controller import sensor_bp
    app.register_blueprint(sensor_bp, url_prefix='/api/sensors')
    logger.info("Registered sensor blueprint")

    # 预测API
    from backend.controllers.forecast_controller import forecast_bp
    app.register_blueprint(forecast_bp, url_prefix='/api/forecasts')
    logger.info("Registered forecast blueprint")

    # 告警API
    from backend.controllers.alarm_controller import alarm_bp
    app.register_blueprint(alarm_bp, url_prefix='/api/alarms')
    logger.info("Registered alarm blueprint")

    # 用户认证
    from backend.controllers.auth_controller import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    logger.info("Registered auth blueprint")

    # MCP服务
    from backend.controllers.mcp_controller import mcp_bp
    app.register_blueprint(mcp_bp, url_prefix='/api/mcp')
    logger.info("Registered MCP blueprint")

def register_error_handlers(app):
    """注册错误处理器"""
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'success': False,
            'error': 'Bad Request',
            'message': str(error.description)
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            'success': False,
            'error': 'Unauthorized',
            'message': 'Authentication required'
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            'success': False,
            'error': 'Forbidden',
            'message': 'Insufficient permissions'
        }), 403
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 'Not Found',
            'message': 'Resource not found'
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return jsonify({
            'success': False,
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500

def register_hooks(app):
    """注册请求钩子"""
    
    @app.before_request
    def log_request():
        if app.config.get('DEBUG'):
            logger.debug(f"{request.method} {request.path} - {request.remote_addr}")
    
    @app.after_request
    def after_request(response):
        # 添加安全头
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        return response

def init_database(app):
    """初始化MySQL数据库"""
    from backend.extensions import db
    from sqlalchemy import inspect
    
    # 测试数据库连接
    try:
        # 尝试连接数据库
        with db.engine.connect() as conn:
            logger.info("Database connection successful")
    except Exception as e:
        logger.error(f"Failed to connect to MySQL database: {e}")
        raise RuntimeError(f"Database connection failed: {e}")
    
    # 检查现有表
    inspector = inspect(db.engine)
    existing_tables = inspector.get_table_names()
    logger.info(f"Found existing tables: {', '.join(existing_tables) if existing_tables else 'none'}")
    
    # 创建所有表
    db.create_all()
    logger.info("Database tables created/verified successfully")
    
    # 如果没有现有表，初始化基础数据
    if not existing_tables:
        logger.info("Initializing base data...")
        init_base_data()
    else:
        logger.info("Database tables already exist, skipping data initialization.")

def init_base_data():
    """初始化基础数据"""
    from backend.models.user import User
    from backend.extensions import db
    
    # 检查是否已存在用户
    existing_admin = User.query.filter_by(username="admin").first()
    if existing_admin:
        logger.info("Admin user already exists")
    else:
        # 创建管理员用户
        admin = User.create(username="admin", password="agrinex123", role="admin")
        db.session.commit()
        logger.info("Created admin user")
    
    # 检查测试用户
    existing_test = User.query.filter_by(username="test").first()
    if existing_test:
        logger.info("Test user already exists")
    else:
        # 创建测试用户
        user = User.create(username="test", password="test123", role="user")
        db.session.commit()
        logger.info("Created test user")
    
    # 可以添加更多初始化数据，如设备、传感器等

# 创建应用实例
app = create_app()

if __name__ == '__main__':
    # 运行开发服务器
    port = int(os.getenv('PORT', 8000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting AgriNex Backend on port {port}")
    logger.info(f"Debug mode: {debug}")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
