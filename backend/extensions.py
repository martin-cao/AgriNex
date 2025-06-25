from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager

# 初始化扩展
db = SQLAlchemy()
jwt = JWTManager()

# JWT 黑名单 (生产环境应该使用 Redis)
blacklisted_tokens = set()

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
        from utils.redis_client import redis_client
        return redis_client.get(key)
    except ImportError:
        return None

def set_cache(key, value, ttl=300):
    """设置Redis缓存，如果Redis不可用则静默失败"""
    try:
        from utils.redis_client import redis_client
        return redis_client.set(key, value, ex=ttl)
    except ImportError:
        return False
