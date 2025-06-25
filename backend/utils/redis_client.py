import redis
from flask import current_app

class RedisClient:
    """Redis客户端封装"""
    
    def __init__(self):
        self.client = None
    
    def init_app(self, app):
        """初始化Redis连接"""
        try:
            redis_url = app.config.get('REDIS_URL', 'redis://localhost:6379/0')
            self.client = redis.from_url(redis_url, decode_responses=True)
            # 测试连接
            self.client.ping()
            app.logger.info(f"Redis connected: {redis_url}")
        except Exception as e:
            app.logger.warning(f"Redis connection failed: {e}")
            self.client = None
    
    def get(self, key):
        """获取缓存"""
        if not self.client:
            return None
        try:
            return self.client.get(key)
        except Exception:
            return None
    
    def set(self, key, value, ex=None):
        """设置缓存"""
        if not self.client:
            return False
        try:
            return self.client.set(key, value, ex=ex)
        except Exception:
            return False
    
    def delete(self, key):
        """删除缓存"""
        if not self.client:
            return False
        try:
            return self.client.delete(key)
        except Exception:
            return False
    
    def exists(self, key):
        """检查key是否存在"""
        if not self.client:
            return False
        try:
            return self.client.exists(key)
        except Exception:
            return False

# 全局Redis实例
redis_client = RedisClient()
