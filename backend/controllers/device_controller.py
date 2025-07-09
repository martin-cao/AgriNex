# backend/controllers/device_controller.py
"""
设备管理控制器 - MySQL Only版本
移除所有Mock数据，只支持真实的数据库操作
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
import logging

# 导入数据库模型
from models.device import Device
from models.sensor import Sensor
from models.reading import Reading
from extensions import db

# 创建蓝图
device_bp = Blueprint('device', __name__)

logger = logging.getLogger(__name__)

# 设备相关API
@device_bp.route('', methods=['GET'])
@device_bp.route('/', methods=['GET'])
def get_devices():
    """获取所有设备"""
    try:
        devices = Device.query.all()
        device_list = []
        for device in devices:
            device_list.append({
                'id': device.id,
                'name': device.name,
                'device_type': device.device_type,
                'location': device.location,
                'status': device.status,
                'created_at': device.created_at.isoformat() if device.created_at else None,
                'updated_at': device.updated_at.isoformat() if device.updated_at else None
            })
        
        return jsonify({
            'success': True,
            'data': device_list,
            'total': len(device_list)
        })
    except Exception as e:
        logger.error("Error getting devices: %s", str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@device_bp.route('/<int:device_id>', methods=['GET'])
def get_device(device_id: int):
    """获取特定设备"""
    try:
        device = Device.query.get(device_id)
        if not device:
            return jsonify({
                'success': False,
                'error': 'Device not found'
            }), 404
        
        device_data = {
            'id': device.id,
            'name': device.name,
            'device_type': device.device_type,
            'location': device.location,
            'status': device.status,
            'created_at': device.created_at.isoformat() if device.created_at else None,
            'updated_at': device.updated_at.isoformat() if device.updated_at else None
        }
        
        return jsonify({
            'success': True,
            'data': device_data
        })
    except Exception as e:
        logger.error("Error getting device %d: %s", device_id, str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# 传感器相关API
@device_bp.route('/<int:device_id>/sensors', methods=['GET'])
def get_device_sensors(device_id: int):
    """获取设备的所有传感器"""
    try:
        # 先检查设备是否存在
        device = Device.query.get(device_id)
        if not device:
            return jsonify({
                'success': False,
                'error': 'Device not found'
            }), 404
        
        sensors = Sensor.query.filter_by(device_id=device_id).all()
        sensor_list = []
        for sensor in sensors:
            sensor_list.append({
                'id': sensor.id,
                'device_id': sensor.device_id,
                'name': sensor.name,
                'sensor_type': sensor.sensor_type,
                'data_type': sensor.data_type,
                'unit': sensor.unit,
                'status': sensor.status,
                'created_at': sensor.created_at.isoformat() if sensor.created_at else None
            })
        
        return jsonify({
            'success': True,
            'data': sensor_list,
            'total': len(sensor_list)
        })
    except Exception as e:
        logger.error("Error getting sensors for device %d: %s", device_id, str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@device_bp.route('/<int:device_id>/sensors/<int:sensor_id>/latest', methods=['GET'])
def get_latest_reading(device_id: int, sensor_id: int):
    """获取传感器最新读数"""
    try:
        # 验证传感器属于指定设备
        sensor = Sensor.query.filter_by(id=sensor_id, device_id=device_id).first()
        if not sensor:
            return jsonify({
                'success': False,
                'error': 'Sensor not found'
            }), 404
        
        # 获取最新读数
        reading = Reading.query.filter_by(sensor_id=sensor_id).order_by(Reading.timestamp.desc()).first()
        if not reading:
            return jsonify({
                'success': False,
                'error': 'No readings found'
            }), 404
        
        reading_data = {
            'id': reading.id,
            'sensor_id': reading.sensor_id,
            'timestamp': reading.timestamp.isoformat(),
            'numeric_value': reading.numeric_value,
            'text_value': reading.text_value,
            'file_path': reading.file_path
        }
        
        return jsonify({
            'success': True,
            'data': reading_data
        })
    except Exception as e:
        logger.error("Error getting latest reading for sensor %d: %s", sensor_id, str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@device_bp.route('/<int:device_id>/sensors/<int:sensor_id>/readings', methods=['GET'])
def get_sensor_readings(device_id: int, sensor_id: int):
    """获取传感器读数列表"""
    try:
        # 验证传感器属于指定设备
        sensor = Sensor.query.filter_by(id=sensor_id, device_id=device_id).first()
        if not sensor:
            return jsonify({
                'success': False,
                'error': 'Sensor not found'
            }), 404
        
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 100, type=int)
        
        # 查询读数
        query = Reading.query.filter_by(sensor_id=sensor_id).order_by(Reading.timestamp.desc())
        total = query.count()
        readings = query.offset((page - 1) * limit).limit(limit).all()
        
        reading_list = []
        for reading in readings:
            reading_list.append({
                'id': reading.id,
                'sensor_id': reading.sensor_id,
                'timestamp': reading.timestamp.isoformat(),
                'numeric_value': reading.numeric_value,
                'text_value': reading.text_value,
                'file_path': reading.file_path
            })
        
        return jsonify({
            'success': True,
            'data': reading_list,
            'total': total,
            'page': page,
            'limit': limit,
            'has_next': (page * limit) < total
        })
    except Exception as e:
        logger.error("Error getting readings for sensor %d: %s", sensor_id, str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# 健康检查
@device_bp.route('/health', methods=['GET'])
def health_check():
    """设备服务健康检查"""
    try:
        # 测试数据库连接
        Device.query.count()
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'message': 'Device service is running without mock data',
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error("Health check failed: %s", str(e))
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500
