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
            "origins": ["http://localhost:80", "http://localhost:3000", "http://localhost:3001", "http://localhost:5173", "http://localhost:8080"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # 配置应用
    from config import Config
    app.config.from_object(Config)
    logger.info("Configuration loaded successfully")
    
    # 初始化扩展
    from extensions import init_extensions
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
    
    # 启动告警监控服务
    try:
        from services.alarm_startup import init_alarm_services
        init_alarm_services(app)
        logger.info("Alarm monitoring services initialized")
    except Exception as e:
        logger.error(f"Failed to initialize alarm services: {e}")
    
    return app

def register_blueprints(app):
    """注册蓝图"""
    # 主要路由
    from controllers.main_controller import main_bp
    app.register_blueprint(main_bp, url_prefix='/api')
    logger.info("Registered main blueprint")

    # 设备管理API
    from controllers.device_controller import device_bp
    app.register_blueprint(device_bp, url_prefix='/api/devices')
    logger.info("Registered device blueprint")

    # 设备模板管理API
    from controllers.device_template_controller import device_template_bp
    app.register_blueprint(device_template_bp, url_prefix='/api/device-templates')
    logger.info("Registered device template blueprint")

    # 传感器API
    from controllers.sensor_controller import sensor_bp
    app.register_blueprint(sensor_bp, url_prefix='/api/sensors')
    logger.info("Registered sensor blueprint")

    # Dashboard API
    from controllers.dashboard_controller import dashboard_bp
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    logger.info("Registered dashboard blueprint")

    # 预测API
    from controllers.forecast_controller import forecast_bp
    app.register_blueprint(forecast_bp, url_prefix='/api/forecasts')
    logger.info("Registered forecast blueprint")

    # 告警API
    from controllers.alarm_controller import alarm_bp
    app.register_blueprint(alarm_bp, url_prefix='/api/alarms')
    logger.info("Registered alarm blueprint")

    # 用户认证
    from controllers.auth_controller import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    logger.info("Registered auth blueprint")

    # LLM智能助手
    from controllers.llm_controller import llm_bp
    app.register_blueprint(llm_bp, url_prefix='/api/llm')
    logger.info("Registered LLM blueprint")

    # MCP服务
    from controllers.mcp_controller import mcp_bp
    app.register_blueprint(mcp_bp, url_prefix='/api/mcp')
    logger.info("Registered MCP blueprint")

    # MQTT服务
    from controllers.mqtt_controller import mqtt_bp
    app.register_blueprint(mqtt_bp, url_prefix='/api/mqtt')
    logger.info("Registered MQTT blueprint")

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
    import os
    
    # 检查是否允许无数据库模式
    if os.getenv('ALLOW_NO_DB', '').lower() == 'true':
        logger.info("Running in no-database mode, skipping database initialization")
        return
    
    from extensions import db
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
    from models.user import User
    from extensions import db
    
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
