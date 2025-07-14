from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, get_jwt
from extensions import db
import os
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

# 开发模式的简单用户验证（生产环境需要替换为数据库）
DEV_USERS = {
    "admin": {"password": "admin123", "role": "admin"},
    "user": {"password": "user123", "role": "user"},
    "demo": {"password": "demo123", "role": "user"}
}

@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({"error": "Username and password required"}), 400
        
        # 如果允许无数据库模式，使用开发模式验证
        if os.getenv('ALLOW_NO_DB', '').lower() == 'true':
            user = DEV_USERS.get(username)
            if user and user['password'] == password:
                access_token = create_access_token(
                    identity=username,
                    additional_claims={"role": user['role']}
                )
                refresh_token = create_refresh_token(identity=username)
                
                return jsonify({
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "user": {
                        "username": username,
                        "role": user['role']
                    }
                }), 200
            else:
                return jsonify({"error": "Invalid credentials"}), 401
        
        # 生产模式：数据库验证
        try:
            from models.user import User
            user = User.find_by_username(username)
            if not user:
                logger.warning("Login attempt with non-existent username: %s", username)
                return jsonify({"error": "Invalid credentials"}), 401
            
            if not user.check_password(password):
                logger.warning("Invalid password for user: %s", username)
                return jsonify({"error": "Invalid credentials"}), 401
            
            # 创建JWT令牌
            access_token = create_access_token(
                identity=str(user.id),
                additional_claims={
                    "username": user.username,
                    "role": user.role
                }
            )
            refresh_token = create_refresh_token(identity=str(user.id))
            
            logger.info("User %s logged in successfully", username)
            
            return jsonify({
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": user.to_dict()
            }), 200
            
        except Exception as db_error:
            logger.error("Database error during login: %s", str(db_error))
            return jsonify({"error": "Database connection error"}), 500
        
    except Exception as e:
        logger.error("Login failed: %s", str(e))
        return jsonify({"error": f"Login failed: {str(e)}"}), 500

@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        username = data.get('username')
        password = data.get('password')
        role = data.get('role', 'user')  # 默认角色为user
        
        if not username or not password:
            return jsonify({"error": "Username and password required"}), 400
            
        # 密码强度验证
        if len(password) < 6:
            return jsonify({"error": "Password must be at least 6 characters long"}), 400
        
        # 角色验证
        if role not in ['user', 'admin']:
            return jsonify({"error": "Invalid role"}), 400
        
        # 开发模式：临时注册（不持久化）
        if os.getenv('ALLOW_NO_DB', '').lower() == 'true':
            if username in DEV_USERS:
                return jsonify({"error": "Username already exists"}), 409
            
            # 临时添加到内存（重启后丢失）
            DEV_USERS[username] = {"password": password, "role": role}
            
            return jsonify({
                "message": "User registered successfully (dev mode - not persistent)",
                "username": username
            }), 201
        
        # 生产模式：数据库注册
        try:
            from models.user import User
            # 检查用户名是否已存在
            existing_user = User.find_by_username(username)
            if existing_user:
                return jsonify({"error": "Username already exists"}), 409
            
            # 创建新用户
            new_user = User.create(username=username, password=password, role=role)
            db.session.commit()
            
            # 自动登录新注册的用户
            access_token = create_access_token(
                identity=str(new_user.id),
                additional_claims={
                    "username": new_user.username,
                    "role": new_user.role
                }
            )
            refresh_token = create_refresh_token(identity=str(new_user.id))
            
            logger.info("New user registered and logged in: %s", username)
            
            return jsonify({
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": new_user.to_dict()
            }), 201
            
        except Exception as db_error:
            db.session.rollback()
            logger.error("Database error during registration: %s", str(db_error))
            return jsonify({"error": "Database connection error"}), 500
        
    except Exception as e:
        logger.error("Registration failed: %s", str(e))
        return jsonify({"error": f"Registration failed: {str(e)}"}), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """刷新访问令牌"""
    try:
        current_user_id = get_jwt_identity()
        
        # 如果是开发模式，直接创建新token
        if os.getenv('ALLOW_NO_DB', '').lower() == 'true':
            new_token = create_access_token(identity=current_user_id)
            return jsonify({
                "access_token": new_token
            }), 200
        
        # 生产模式：验证用户是否仍然存在
        try:
            from models.user import User
            user = User.query.get(int(current_user_id))
            if not user:
                return jsonify({"error": "User not found"}), 401
            
            new_token = create_access_token(
                identity=str(user.id),
                additional_claims={
                    "username": user.username,
                    "role": user.role
                }
            )
            
            return jsonify({
                "access_token": new_token
            }), 200
            
        except ValueError:
            # 处理无效的用户ID
            return jsonify({"error": "Invalid user"}), 401
        
    except Exception as e:
        logger.error("Token refresh failed: %s", str(e))
        return jsonify({"error": "Token refresh failed"}), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """用户登出"""
    try:
        jti = get_jwt()['jti']
        
        # 将token加入黑名单
        from extensions import revoke_token
        revoke_token(jti)
        
        logger.info("User logged out successfully")
        return jsonify({"message": "Successfully logged out"}), 200
        
    except Exception as e:
        logger.error("Logout failed: %s", str(e))
        return jsonify({"error": "Logout failed"}), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    """获取用户信息"""
    try:
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        
        # 开发模式
        if os.getenv('ALLOW_NO_DB', '').lower() == 'true':
            user_data = DEV_USERS.get(current_user_id, {})
            return jsonify({
                "username": current_user_id,
                "role": user_data.get('role', 'user'),
                "claims": claims
            }), 200
        
        # 生产模式：从数据库获取用户信息
        try:
            from models.user import User
            user = User.query.get(int(current_user_id))
            if not user:
                return jsonify({"error": "User not found"}), 401
                
            return jsonify({
                "user": user.to_dict(),
                "claims": claims
            }), 200
            
        except ValueError:
            return jsonify({"error": "Invalid user"}), 401
        
    except Exception as e:
        logger.error("Profile retrieval failed: %s", str(e))
        return jsonify({"error": "Profile retrieval failed"}), 500
