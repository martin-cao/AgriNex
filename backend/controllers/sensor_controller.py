from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.sensor import Sensor
from models.reading import Reading
from models.device import Device
from models.device_template import DeviceTemplate
from services.sensor_service import SensorService
from extensions import db

sensor_bp = Blueprint('sensor', __name__, url_prefix='/api/sensors')

@sensor_bp.route('/', methods=['GET'])
@jwt_required()
def list_sensors():
    """获取所有传感器"""
    try:
        sensors = Sensor.query.all()
        return jsonify({
            'success': True,
            'data': [sensor.to_dict() for sensor in sensors]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@sensor_bp.route('/<int:sensor_id>', methods=['GET'])
@jwt_required()
def get_sensor(sensor_id):
    """获取特定传感器"""
    sensor = Sensor.query.get_or_404(sensor_id)
    return jsonify({
        'success': True,
        'data': sensor.to_dict()
    })

@sensor_bp.route('/<int:sensor_id>/readings', methods=['GET'])
@jwt_required()
def get_sensor_readings(sensor_id):
    """获取传感器读数"""
    sensor = Sensor.query.get_or_404(sensor_id)
    
    # 分页参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 100, type=int)
    
    # 时间范围
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    
    query = Reading.query.filter_by(sensor_id=sensor_id)
    
    if start_time:
        from datetime import datetime
        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        query = query.filter(Reading.timestamp >= start_dt)
    
    if end_time:
        from datetime import datetime
        end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        query = query.filter(Reading.timestamp <= end_dt)
    
    readings = query.order_by(Reading.timestamp.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'success': True,
        'data': [reading.to_dict() for reading in readings.items],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': readings.total,
            'pages': readings.pages,
            'has_next': readings.has_next,
            'has_prev': readings.has_prev
        }
    })

@sensor_bp.route('/<int:sensor_id>/readings', methods=['POST'])
@jwt_required()
def create_reading(sensor_id):
    """创建传感器读数"""
    sensor = Sensor.query.get_or_404(sensor_id)
    data = request.get_json()
    
    try:
        data_type = data.get('data_type', 'numeric')
        
        if data_type == 'numeric':
            reading = Reading.create_numeric(
                sensor_id=sensor_id,
                value=data['value'],
                unit=data.get('unit'),
                metadata=data.get('metadata')
            )
        else:
            # 文件型数据处理在单独的文件上传接口中
            return jsonify({
                'success': False,
                'error': 'File uploads should use the file upload endpoint'
            }), 400
        
        db.session.add(reading)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': reading.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@sensor_bp.route('/<int:sensor_id>/readings/latest', methods=['GET'])
@jwt_required()
def get_latest_reading(sensor_id):
    """获取传感器最新读数"""
    sensor = Sensor.query.get_or_404(sensor_id)
    
    reading = Reading.query.filter_by(sensor_id=sensor_id)\
                    .order_by(Reading.timestamp.desc())\
                    .first()
    
    if not reading:
        return jsonify({
            'success': False,
            'message': 'No readings found'
        }), 404
    
    return jsonify({
        'success': True,
        'data': reading.to_dict()
    })

@sensor_bp.route('/<int:sensor_id>/statistics', methods=['GET'])
@jwt_required()
def get_sensor_statistics(sensor_id):
    """获取传感器统计信息"""
    sensor = Sensor.query.get_or_404(sensor_id)
    
    # 获取统计信息
    from sqlalchemy import func
    
    stats = db.session.query(
        func.count(Reading.id).label('total_readings'),
        func.avg(Reading.numeric_value).label('avg_value'),
        func.min(Reading.numeric_value).label('min_value'),
        func.max(Reading.numeric_value).label('max_value'),
        func.min(Reading.timestamp).label('first_reading'),
        func.max(Reading.timestamp).label('last_reading')
    ).filter(
        Reading.sensor_id == sensor_id,
        Reading.data_type == 'numeric'
    ).first()
    
    return jsonify({
        'success': True,
        'data': {
            'sensor_id': sensor_id,
            'sensor_name': sensor.name,
            'sensor_type': sensor.type,
            'unit': sensor.unit,
            'total_readings': stats.total_readings or 0,
            'average_value': float(stats.avg_value) if stats.avg_value else None,
            'min_value': float(stats.min_value) if stats.min_value else None,
            'max_value': float(stats.max_value) if stats.max_value else None,
            'first_reading': stats.first_reading.isoformat() if stats.first_reading else None,
            'last_reading': stats.last_reading.isoformat() if stats.last_reading else None
        }
    })

@sensor_bp.route('/', methods=['POST'])
@jwt_required()
def create_sensor():
    """创建传感器 - 必须关联到有效设备并符合设备模板"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # 验证必需字段
        required_fields = ['device_id', 'sensor_type']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # 验证设备存在
        device = Device.query.get(data['device_id'])
        if not device:
            return jsonify({
                'success': False,
                'error': f'Device with ID {data["device_id"]} not found'
            }), 404
        
        # 验证设备是否处于活跃状态
        if not device.is_active:
            return jsonify({
                'success': False,
                'error': 'Cannot add sensors to inactive devices'
            }), 400
        
        # 获取设备模板
        device_template = DeviceTemplate.get_by_device_type(device.type)
        if not device_template:
            return jsonify({
                'success': False,
                'error': f'No template found for device type: {device.type}'
            }), 400
        
        # 验证传感器类型是否在设备模板中定义
        if not device_template.validate_sensor_type(data['sensor_type']):
            allowed_types = [config['type'] for config in device_template.get_sensor_configs()]
            return jsonify({
                'success': False,
                'error': f'Sensor type "{data["sensor_type"]}" is not allowed for device type "{device.type}". Allowed types: {allowed_types}'
            }), 400
        
        # 检查是否已存在相同类型的传感器
        existing_sensor = Sensor.query.filter_by(
            device_id=data['device_id'],
            type=data['sensor_type']
        ).first()
        
        if existing_sensor:
            return jsonify({
                'success': False,
                'error': f'Sensor of type "{data["sensor_type"]}" already exists for device {device.name}'
            }), 400
        
        # 从设备模板获取传感器配置
        sensor_configs = device_template.get_sensor_configs()
        sensor_template = next((config for config in sensor_configs 
                               if config['type'] == data['sensor_type']), None)
        
        # 创建传感器
        sensor = Sensor.create(
            device_id=data['device_id'],
            sensor_type=data['sensor_type'],
            name=data.get('name', sensor_template['name'] if sensor_template else data['sensor_type']),
            unit=data.get('unit', sensor_template['unit'] if sensor_template else ''),
            status=data.get('status', 'active')
        )
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': sensor.to_dict(),
            'message': f'Sensor created successfully for device {device.name}'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
