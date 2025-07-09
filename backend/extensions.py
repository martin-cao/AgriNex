from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
import logging

logger = logging.getLogger(__name__)

# 初始化扩展
db = SQLAlchemy()
jwt = JWTManager()

# JWT 黑名单 (生产环境应该使用 Redis)
blacklisted_tokens = set()

def init_extensions(app):
    """初始化所有Flask扩展"""
    db.init_app(app)
    jwt.init_app(app)
    
    # 初始化MQTT服务
    from backend.services.mqtt_service import mqtt_service
    mqtt_service.init_app(app)
    
    # 启动MQTT连接（在应用上下文中）
    import threading
    import time
    
    def start_mqtt_with_context():
        """在应用上下文中启动MQTT服务"""
        time.sleep(1)  # 等待其他服务初始化完成
        with app.app_context():
            success = mqtt_service.connect()
            if success:
                logger.info("MQTT服务初始化成功")
            else:
                logger.error("MQTT服务初始化失败")
    
    mqtt_thread = threading.Thread(target=start_mqtt_with_context)
    mqtt_thread.daemon = True
    mqtt_thread.start()

@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    jti = jwt_payload['jti']
    return jti in blacklisted_tokens

def revoke_token(jti):
    blacklisted_tokens.add(jti)

# Redis缓存工具函数
def get_from_cache(key):
    """从Redis获取缓存，如果Redis不可用则返回None"""
    try:
        from backend.utils.redis_client import redis_client
        return redis_client.get(key)
    except ImportError:
        return None

def set_cache(key, value, ttl=300):
    """设置Redis缓存，如果Redis不可用则静默失败"""
    try:
        from backend.utils.redis_client import redis_client
        return redis_client.set(key, value, ex=ttl)
    except ImportError:
        return False
