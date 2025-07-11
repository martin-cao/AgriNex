from flask import Blueprint, request, jsonify
from datetime import datetime
import os

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """主页"""
    return jsonify({
        'name': 'AgriNex - 农业物联网数据管理平台',
        'description': '支持三层架构和对象存储的现代化农业IoT平台',
        'features': [
            'Device-Sensor-Reading三层架构',
            'MinIO对象存储集成',
            '多类型传感器支持（数值型、图片、视频）',
            'RESTful API',
            'JWT认证',
            'MCP服务集成'
        ],
        'endpoints': {
            'devices': '/api/devices',
            'auth': '/api/auth',
            'mcp': '/api/mcp',
            'health': '/api/health',
            'docs': '/api/docs'
        }
    })

@main_bp.route('/')
def api_info():
    """API信息"""
    return jsonify({
        'title': 'AgriNex API',
        'description': '农业物联网数据管理平台API',
        'base_url': request.url_root,
        'documentation': f"{request.url_root}api/docs"
    })

@main_bp.route('/api/docs')
def api_docs():
    """API文档"""
    return jsonify({
        'title': 'AgriNex API Documentation',
        'description': '农业物联网数据管理平台API文档',
        'base_url': f"{request.url_root}api",
        'endpoints': {
            'devices': {
                'list': 'GET /devices',
                'create': 'POST /devices',
                'get': 'GET /devices/{id}',
                'update': 'PUT /devices/{id}',
                'delete': 'DELETE /devices/{id}',
                'overview': 'GET /devices/{id}/overview',
                'sensors': 'GET /devices/{id}/sensors',
                'readings': 'GET /devices/{id}/readings',
                'statistics': 'GET /devices/{id}/statistics',
                'health': 'GET /devices/{id}/health'
            },
            'sensors': {
                'create': 'POST /devices/{device_id}/sensors',
                'readings': 'POST /devices/{device_id}/sensors/{sensor_id}/readings'
            },
            'readings': {
                'download': 'GET /devices/readings/{id}/download'
            }
        },
        'data_types': {
            'numeric': '数值型传感器数据（温度、湿度、光照等）',
            'image': '图片数据（摄像头、显微镜等）',
            'video': '视频数据（监控录像等）'
        },
        'storage': {
            'primary': 'MinIO对象存储',
            'backup': '本地文件系统',
            'features': ['自动缩略图生成', '文件元数据', '预签名URL']
        }
    })

@main_bp.route('/health')
def health_check():
    """健康检查端点"""
    try:
        # 检查数据库连接
        from extensions import db
        with db.engine.connect() as conn:
            conn.execute(db.text('SELECT 1'))
        
        # 检查MQTT服务状态
        mqtt_status = 'unknown'
        try:
            from services.mqtt_service import mqtt_service
            mqtt_status = mqtt_service.get_connection_status()
        except Exception:
            mqtt_status = 'unavailable'
        
        # 检查告警监控状态
        alarm_status = 'unknown'
        try:
            from services.alarm_monitor import alarm_monitor
            alarm_status = 'running' if alarm_monitor.is_running else 'stopped'
        except Exception:
            alarm_status = 'unavailable'
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'services': {
                'database': 'connected',
                'mqtt': mqtt_status,
                'alarm_monitor': alarm_status
            },
            'version': '2.0.0'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }), 503

@main_bp.route('/api/status')
def system_status():
    """系统状态"""
    status = {
        'status': 'running',
        'timestamp': datetime.utcnow().isoformat(),
        'components': {}
    }
    
    # 检查数据库连接
    try:
        from extensions import db
        with db.engine.connect() as conn:
            conn.execute(db.text('SELECT 1'))
        status['components']['database'] = 'connected'
    except Exception as e:
        status['components']['database'] = f'error: {str(e)}'
    
    # 检查MinIO连接
    try:
        from services.storage_service import storage_service
        if storage_service.minio_client:
            # 尝试列出bucket
            list(storage_service.minio_client.list_buckets())
            status['components']['minio'] = 'connected'
        else:
            status['components']['minio'] = 'not_configured'
    except Exception as e:
        status['components']['minio'] = f'error: {str(e)}'
    
    # 检查本地存储
    try:
        from flask import current_app
        storage_path = current_app.config.get('LOCAL_STORAGE_PATH', './storage')
        if os.path.exists(storage_path) and os.access(storage_path, os.W_OK):
            status['components']['local_storage'] = 'available'
        else:
            status['components']['local_storage'] = 'not_accessible'
    except Exception as e:
        status['components']['local_storage'] = f'error: {str(e)}'
    
    # 检查MQTT连接
    try:
        from services.mqtt_service import mqtt_service
        mqtt_status = mqtt_service.get_connection_status()
        if mqtt_status.get('connected', False):
            status['components']['mqtt'] = 'connected'
        else:
            status['components']['mqtt'] = 'disconnected'
    except Exception as e:
        status['components']['mqtt'] = f'error: {str(e)}'
    
    return jsonify(status)
