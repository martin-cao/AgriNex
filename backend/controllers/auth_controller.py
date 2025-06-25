from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, get_jwt
import os

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
        
        # 开发模式：简单验证
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
        
        # TODO: 生产模式数据库验证
        return jsonify({"error": "Database authentication not implemented"}), 501
        
    except Exception as e:
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
        
        if not username or not password:
            return jsonify({"error": "Username and password required"}), 400
        
        # 开发模式：临时注册（不持久化）
        if os.getenv('ALLOW_NO_DB', '').lower() == 'true':
            if username in DEV_USERS:
                return jsonify({"error": "Username already exists"}), 409
            
            # 临时添加到内存（重启后丢失）
            DEV_USERS[username] = {"password": password, "role": "user"}
            
            return jsonify({
                "message": "User registered successfully (dev mode - not persistent)",
                "username": username
            }), 201
        
        # TODO: 生产模式数据库注册
        return jsonify({"error": "Database registration not implemented"}), 501
        
    except Exception as e:
        return jsonify({"error": f"Registration failed: {str(e)}"}), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """刷新访问令牌"""
    try:
        current_user = get_jwt_identity()
        new_token = create_access_token(identity=current_user)
        
        return jsonify({
            "access_token": new_token
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Token refresh failed: {str(e)}"}), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """用户登出"""
    try:
        jti = get_jwt()['jti']
        current_user = get_jwt_identity()
        
        # TODO: 将token加入黑名单
        # token_blacklist_service.revoke_token(jti, current_user, expires_at)
        
        return jsonify({"message": "Successfully logged out"}), 200
        
    except Exception as e:
        return jsonify({"error": f"Logout failed: {str(e)}"}), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    """获取用户信息"""
    try:
        current_user = get_jwt_identity()
        claims = get_jwt()
        
        # 开发模式
        if os.getenv('ALLOW_NO_DB', '').lower() == 'true':
            user_data = DEV_USERS.get(current_user, {})
            return jsonify({
                "username": current_user,
                "role": user_data.get('role', 'user'),
                "claims": claims
            }), 200
        
        # TODO: 从数据库获取用户信息
        return jsonify({"error": "Database profile not implemented"}), 501
        
    except Exception as e:
        return jsonify({"error": f"Profile fetch failed: {str(e)}"}), 500
