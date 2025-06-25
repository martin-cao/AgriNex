import os
from datetime import timedelta

class Config:
    # Flask 配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # 数据库配置（支持降级到SQLite）
    DATABASE_URL = os.getenv('DATABASE_URL')
    if DATABASE_URL:
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        # 降级到SQLite（开发模式）
        if os.getenv('ALLOW_NO_DB', '').lower() == 'true':
            SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # 内存数据库
        else:
            SQLALCHEMY_DATABASE_URI = 'sqlite:///agrinex.db'  # 文件数据库
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }

    # JWT 配置
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', '900')))  # 15分钟
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(seconds=int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', '604800')))  # 7天
    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = ['access', 'refresh']
    
    # MQTT 配置
    MQTT_HOST = os.getenv('MQTT_HOST', 'localhost')
    MQTT_PORT = int(os.getenv('MQTT_PORT', '1883'))
    MQTT_USERNAME = os.getenv('MQTT_USERNAME', '')
    MQTT_PASSWORD = os.getenv('MQTT_PASSWORD', '')
    MQTT_KEEPALIVE = int(os.getenv('MQTT_KEEPALIVE', '60'))
    
    # OpenAI 配置
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o')
    OPENAI_MAX_TOKENS = int(os.getenv('OPENAI_MAX_TOKENS', '512'))
    
    # Redis 配置 (用于缓存和限流)
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # 应用配置
    ITEMS_PER_PAGE = 100
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB 最大文件上传
