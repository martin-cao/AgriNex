import os

class Config:
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'mysql://root:password@localhost/agriot')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT 密钥
    JWT_SECRET_KEY = 'your_jwt_secret_key'
