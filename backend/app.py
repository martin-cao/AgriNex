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
    
    # 加载配置
    try:
        from config import Config
        app.config.from_object(Config)
        logger.info("Configuration loaded successfully")
    except ImportError as e:
        logger.warning(f"Failed to load config: {e}. Using default settings.")
        app.config.update({
            'SECRET_KEY': 'dev-secret-key',
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///agrinex.db',
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
            'JWT_SECRET_KEY': 'jwt-secret-key',
            'JWT_ACCESS_TOKEN_EXPIRES': 900
        })
    
    # 初始化扩展
    try:
        from extensions import db, jwt
        db.init_app(app)
        jwt.init_app(app)
        logger.info("Extensions initialized successfully")
    except ImportError as e:
        logger.warning(f"Failed to initialize extensions: {e}")
    
    # 注册蓝图
    register_blueprints(app)
    
    # 创建数据库表
    with app.app_context():
        try:
            db.create_all()
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
    
    # 注册错误处理器
    register_error_handlers(app)
    
    # 注册钩子函数
    register_hooks(app)
    
    return app

def register_blueprints(app):
    """注册蓝图"""
    try:
        # 主要路由
        from controllers.main_controller import main_bp
        app.register_blueprint(main_bp)
        logger.info("Registered main blueprint")
        
        # 设备管理API
        from controllers.device_controller_unified import device_bp
        app.register_blueprint(device_bp)
        logger.info("Registered device blueprint")
        
        # 传感器API
        try:
            from controllers.sensor_controller import sensor_bp
            app.register_blueprint(sensor_bp)
            logger.info("Registered sensor blueprint")
        except ImportError:
            logger.warning("Sensor controller not available")
        
        # 预测API
        try:
            from controllers.forecast_controller import forecast_bp
            app.register_blueprint(forecast_bp)
            logger.info("Registered forecast blueprint")
        except ImportError:
            logger.warning("Forecast controller not available")
        
        # 告警API
        try:
            from controllers.alarm_controller import alarm_bp
            app.register_blueprint(alarm_bp)
            logger.info("Registered alarm blueprint")
        except ImportError:
            logger.warning("Alarm controller not available")
        
        # 用户认证
        try:
            from controllers.auth_controller import auth_bp
            app.register_blueprint(auth_bp, url_prefix='/api/auth')
            logger.info("Registered auth blueprint")
        except ImportError:
            logger.warning("Auth controller not available")
        
        # MCP服务
        try:
            from controllers.mcp_controller import mcp_bp
            app.register_blueprint(mcp_bp, url_prefix='/api/mcp')
            logger.info("Registered MCP blueprint")
        except ImportError:
            logger.warning("MCP controller not available")
            
    except ImportError as e:
        logger.error(f"Failed to register blueprints: {e}")
        
        # 注册基本的健康检查路由作为fallback
        @app.route('/api/health')
        def health_check():
            return jsonify({
                'status': 'ok',
                'message': 'AgriNex Backend is running',
                'timestamp': datetime.utcnow().isoformat()
            })

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
