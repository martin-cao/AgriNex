# backend/controllers/device_controller.py - 合并版本
# mypy: disable-error-code=misc,union-attr,name-defined
from flask import Blueprint, request, jsonify, send_file
from datetime import datetime, timedelta
from typing import Optional
import logging
import os
import random
import math

# 尝试导入服务层
try:
    from backend.services.device_service import DeviceService
    from backend.services.sensor_service import SensorService
    from backend.services.reading_service import ReadingService
    from backend.services.storage_service import storage_service
    HAS_SERVICES = True
except ImportError:
    HAS_SERVICES = False
    logging.warning("Services not available, using mock mode")

# 尝试导入数据库模型
try:
    from models.reading import Reading
    from models.device import Device
    from models.sensor import Sensor
    HAS_DB_MODELS = True
except ImportError:
    HAS_DB_MODELS = False
    Reading = None
    Device = None
    Sensor = None
    logging.warning("Database models not available, using mock data")

# 创建蓝图 - 支持多种URL前缀
device_bp = Blueprint('device', __name__)

# Mock data for development - 合并所有版本的Mock数据
MOCK_DEVICES = [
    {"id": 1, "name": "温室1", "device_type": "greenhouse", "type": "greenhouse", "location": "温室区域A", "status": "online"},
    {"id": 2, "name": "温室2", "device_type": "greenhouse", "type": "greenhouse", "location": "温室区域B", "status": "offline"}
]

MOCK_SENSORS = [
    {
        "id": 1, 
        "device_id": 1, 
        "name": "温度传感器", 
        "sensor_type": "temperature", 
        "type": "temperature",
        "data_type": "numeric", 
        "unit": "°C", 
        "status": "active"
    },
    {
        "id": 2, 
        "device_id": 1, 
        "name": "湿度传感器", 
        "sensor_type": "humidity", 
        "type": "humidity",
        "data_type": "numeric", 
        "unit": "%", 
        "status": "active"
    },
    {
        "id": 3, 
        "device_id": 1, 
        "name": "摄像头", 
        "sensor_type": "camera", 
        "type": "camera",
        "data_type": "image", 
        "unit": None, 
        "status": "active"
    },
    {
        "id": 4, 
        "device_id": 2, 
        "name": "光照传感器", 
        "sensor_type": "light", 
        "type": "light",
        "data_type": "numeric", 
        "unit": "lux", 
        "status": "active"
    }
]

def get_mock_readings(sensor_id: int, limit: int = 100, hours: int = 24):
    """生成模拟读数数据 - 合并版本"""
    readings = []
    sensor = next((s for s in MOCK_SENSORS if s['id'] == sensor_id), None)
    if not sensor:
        return []
    
    now = datetime.utcnow()
    # 根据参数确定数据点数量
    data_points = min(limit, hours * 6) if hours else limit
    
    for i in range(data_points):
        timestamp = now - timedelta(minutes=i * 10)
        
        if sensor.get('data_type') == 'numeric' or sensor.get('type') in ['temperature', 'humidity', 'light']:
            # 数值型传感器数据生成
            sensor_type = sensor.get('sensor_type') or sensor.get('type')
            
            if sensor_type == 'temperature':
                value = 20 + 10 * random.random() + 3 * math.sin(i * 0.1)
            elif sensor_type == 'humidity':
                value = 40 + 30 * random.random() + 10 * math.sin(i * 0.05)
            elif sensor_type == 'light':
                hour_of_day = timestamp.hour
                if 6 <= hour_of_day <= 18:
                    value = 500 + 1000 * random.random()
                else:
                    value = 0 + 50 * random.random()
            else:
                value = random.uniform(0, 100)
                
            # 支持两种格式的读数
            reading = {
                'id': i + 1,
                'sensor_id': sensor_id,
                'device_id': sensor['device_id'],
                'timestamp': timestamp.isoformat(),
                'value': round(value, 2),  # 兼容旧版本
                'numeric_value': round(value, 2),  # 新版本
                'data_type': 'numeric',
                'metadata': {}
            }
        else:
            # 多媒体数据
            reading = {
                'id': i + 1,
                'sensor_id': sensor_id,
                'device_id': sensor['device_id'],
                'data_type': sensor.get('data_type', 'image'),
                'file_path': f'/mock/images/device_{sensor["device_id"]}_sensor_{sensor_id}_{i}.jpg',
                'file_format': 'jpg',
                'file_size': random.randint(50000, 200000),
                'timestamp': timestamp.isoformat(),
                'metadata': {'width': 1920, 'height': 1080}
            }
            
        readings.append(reading)
    
    return readings[::-1]  # 按时间正序返回

# ==================== 兼容性路由 - 支持旧版本API ====================

@device_bp.route('/devices', methods=['GET'])
def get_devices_legacy():
    """获取设备列表 - 兼容旧版本"""
    return get_devices()

@device_bp.route('/devices/<int:device_id>/sensors', methods=['GET'])
def get_sensors_legacy(device_id):
    """获取设备传感器 - 兼容旧版本"""
    return get_device_sensors(device_id)

@device_bp.route('/sensors/<int:sensor_id>/readings/latest', methods=['GET'])
def get_latest_reading_legacy(sensor_id):
    """获取传感器最新读数 - 兼容旧版本"""
    if os.getenv('ALLOW_NO_DB', '').lower() == 'true' or not HAS_DB_MODELS:
        mock_readings = get_mock_readings(sensor_id, 1)
        if mock_readings:
            return jsonify(mock_readings[-1])
        return jsonify({'error': 'No data available'}), 404
    
    if HAS_DB_MODELS and Reading:
        reading = Reading.query.filter_by(sensor_id=sensor_id).order_by(Reading.timestamp.desc()).first()
        if reading:
            return jsonify(reading.to_dict())
    
    return jsonify({'error': 'No data available'}), 404

@device_bp.route('/sensors/<int:sensor_id>/readings', methods=['GET'])
def get_readings_legacy(sensor_id):
    """获取传感器历史读数 - 兼容旧版本"""
    limit = request.args.get('limit', 100, type=int)
    page = request.args.get('page', 1, type=int)
    
    if os.getenv('ALLOW_NO_DB', '').lower() == 'true' or not HAS_DB_MODELS:
        mock_readings = get_mock_readings(sensor_id, limit * page, 24)
        start = (page - 1) * limit
        end = start + limit
        paginated_readings = mock_readings[start:end]
        return jsonify(paginated_readings)
    
    if HAS_DB_MODELS and Reading:
        readings = Reading.query.filter_by(sensor_id=sensor_id).order_by(Reading.timestamp.desc()).paginate(
            page=page, per_page=limit, error_out=False)
        return jsonify([r.to_dict() for r in readings.items])
    
    return jsonify([])

@device_bp.route('/sensors/<int:sensor_id>/stats', methods=['GET'])
def get_sensor_stats_legacy(sensor_id):
    """获取传感器统计信息 - 兼容旧版本"""
    if os.getenv('ALLOW_NO_DB', '').lower() == 'true' or not HAS_DB_MODELS:
        mock_readings = get_mock_readings(sensor_id, 144, 24)  # 24小时数据
        if not mock_readings:
            return jsonify({'error': 'No data available'}), 404
        
        values = [r.get('value') or r.get('numeric_value') for r in mock_readings if r.get('value') is not None or r.get('numeric_value') is not None]
        sensor = next((s for s in MOCK_SENSORS if s['id'] == sensor_id), None)
        
        if not values:
            return jsonify({'error': 'No numeric data available'}), 404
            
        stats = {
            'sensor_id': sensor_id,
            'type': sensor.get('type') or sensor.get('sensor_type', 'value') if sensor else 'value',
            'min': min(values),
            'max': max(values),
            'avg': sum(values) / len(values),
            'count': len(values)
        }
        return jsonify(stats)
    
    if HAS_DB_MODELS and Reading:
        readings = Reading.query.filter_by(sensor_id=sensor_id).all()
        if not readings:
            return jsonify({'error': 'No data available'}), 404
        
        values = [r.value for r in readings if r.value is not None]
        if not values:
            return jsonify({'error': 'No numeric data available'}), 404
            
        stats = {
            'sensor_id': sensor_id,
            'min': min(values),
            'max': max(values),
            'avg': sum(values) / len(values),
            'count': len(values)
        }
        return jsonify(stats)
    
    return jsonify({'error': 'No data available'}), 404

# ==================== 新版本API (RESTful) ====================

@device_bp.route('/api/devices', methods=['GET'])
@device_bp.route('', methods=['GET'])
def get_devices():
    """获取设备列表"""
    try:
        # 获取查询参数
        device_type = request.args.get('type')
        status = request.args.get('status')
        search = request.args.get('search')
        
        if not HAS_SERVICES:
            # Mock 模式
            devices = MOCK_DEVICES.copy()
            if device_type:
                devices = [d for d in devices if d.get('device_type') == device_type or d.get('type') == device_type]
            if status:
                devices = [d for d in devices if d.get('status') == status]
            if search:
                devices = [d for d in devices if search.lower() in d.get('name', '').lower()]
            
            # 检查是否为旧版本API调用
            if '/api/devices' not in request.path:
                return jsonify({"devices": devices, "total": len(devices)})
            
            return jsonify({
                'success': True,
                'data': devices,
                'total': len(devices)
            })
        
        # 使用服务层
        if search:
            devices = DeviceService.search_devices(search, device_type, status)
        elif device_type:
            devices = DeviceService.get_devices_by_type(device_type)
        elif status:
            devices = DeviceService.get_all_devices(status)
        else:
            devices = DeviceService.get_all_devices()
        
        device_list = [device.to_dict() for device in devices]
        
        # 检查是否为旧版本API调用
        if '/api/devices' not in request.path:
            return jsonify(device_list)
        
        return jsonify({
            'success': True,
            'data': device_list,
            'total': len(device_list)
        })
        
    except Exception as e:
        logging.error(f"Failed to get devices: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@device_bp.route('/api/devices/<int:device_id>', methods=['GET'])
def get_device(device_id):
    """获取设备详情"""
    try:
        if not HAS_SERVICES:
            # Mock 模式
            device = next((d for d in MOCK_DEVICES if d['id'] == device_id), None)
            if not device:
                return jsonify({'success': False, 'error': 'Device not found'}), 404
            return jsonify({'success': True, 'data': device})
        
        device = DeviceService.get_device_by_id(device_id)
        if not device:
            return jsonify({'success': False, 'error': 'Device not found'}), 404
        
        return jsonify({
            'success': True,
            'data': device.to_dict()
        })
        
    except Exception as e:
        logging.error(f"Failed to get device {device_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@device_bp.route('/api/devices', methods=['POST'])
def create_device():
    """创建设备"""
    try:
        data = request.get_json()
        
        # 验证必要字段
        required_fields = ['name', 'device_type', 'location']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        if not HAS_SERVICES:
            # Mock 模式
            new_device = {
                'id': max([d['id'] for d in MOCK_DEVICES]) + 1,
                'name': data['name'],
                'device_type': data['device_type'],
                'type': data['device_type'],  # 兼容性
                'location': data['location'],
                'status': 'offline',
                'description': data.get('description'),
                'created_at': datetime.utcnow().isoformat()
            }
            MOCK_DEVICES.append(new_device)
            return jsonify({'success': True, 'data': new_device}), 201
        
        device = DeviceService.create_device(
            name=data['name'],
            device_type=data['device_type'],
            location=data['location'],
            description=data.get('description'),
            config=data.get('config', {})
        )
        
        return jsonify({
            'success': True,
            'data': device.to_dict()
        }), 201
        
    except Exception as e:
        logging.error(f"Failed to create device: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@device_bp.route('/api/devices/<int:device_id>', methods=['PUT'])
def update_device(device_id):
    """更新设备"""
    try:
        data = request.get_json()
        
        if not HAS_SERVICES:
            # Mock 模式
            device = next((d for d in MOCK_DEVICES if d['id'] == device_id), None)
            if not device:
                return jsonify({'success': False, 'error': 'Device not found'}), 404
            
            device.update(data)
            return jsonify({'success': True, 'data': device})
        
        device = DeviceService.update_device(device_id, **data)
        if not device:
            return jsonify({'success': False, 'error': 'Device not found'}), 404
        
        return jsonify({
            'success': True,
            'data': device.to_dict()
        })
        
    except Exception as e:
        logging.error(f"Failed to update device {device_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@device_bp.route('/api/devices/<int:device_id>', methods=['DELETE'])
def delete_device(device_id):
    """删除设备"""
    try:
        if not HAS_SERVICES:
            # Mock 模式
            global MOCK_DEVICES
            MOCK_DEVICES = [d for d in MOCK_DEVICES if d['id'] != device_id]
            return jsonify({'success': True, 'message': 'Device deleted'})
        
        success = DeviceService.delete_device(device_id)
        if not success:
            return jsonify({'success': False, 'error': 'Device not found'}), 404
        
        return jsonify({'success': True, 'message': 'Device deleted'})
        
    except Exception as e:
        logging.error(f"Failed to delete device {device_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@device_bp.route('/api/devices/<int:device_id>/overview', methods=['GET'])
def get_device_overview(device_id):
    """获取设备概览"""
    try:
        if not HAS_SERVICES:
            # Mock 模式
            device = next((d for d in MOCK_DEVICES if d['id'] == device_id), None)
            if not device:
                return jsonify({'success': False, 'error': 'Device not found'}), 404
            
            sensors = [s for s in MOCK_SENSORS if s['device_id'] == device_id]
            latest_readings = []
            for sensor in sensors:
                reading = get_mock_readings(sensor['id'], 1)
                if reading:
                    latest_readings.extend(reading)
            
            overview = {
                'device': device,
                'sensors': sensors,
                'latest_readings': latest_readings,
                'statistics': {
                    'total_sensors': len(sensors),
                    'active_sensors': len([s for s in sensors if s['status'] == 'active']),
                    'total_readings': len(latest_readings) * 100,  # Mock
                    'numeric_sensors': len([s for s in sensors if s.get('data_type') == 'numeric']),
                    'multimedia_sensors': len([s for s in sensors if s.get('data_type') in ['image', 'video']])
                }
            }
            return jsonify({'success': True, 'data': overview})
        
        overview = DeviceService.get_device_overview(device_id)
        if not overview:
            return jsonify({'success': False, 'error': 'Device not found'}), 404
        
        return jsonify({'success': True, 'data': overview})
        
    except Exception as e:
        logging.error(f"Failed to get device overview {device_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== 传感器管理 API ====================

@device_bp.route('/api/devices/<int:device_id>/sensors', methods=['GET'])
def get_device_sensors(device_id):
    """获取设备的传感器列表"""
    try:
        data_type = request.args.get('data_type')
        
        if not HAS_SERVICES:
            # Mock 模式
            sensors = [s for s in MOCK_SENSORS if s['device_id'] == device_id]
            if data_type:
                sensors = [s for s in sensors if s.get('data_type') == data_type]
            
            # 检查是否为旧版本API调用
            if '/api/devices' not in request.path:
                return jsonify(sensors)
            
            return jsonify({'success': True, 'data': sensors})
        
        if data_type:
            sensors = DeviceService.get_device_sensors_by_type(device_id, data_type)
        else:
            sensors = SensorService.get_sensors_by_device(device_id)
        
        sensor_list = [sensor.to_dict() for sensor in sensors]
        
        # 检查是否为旧版本API调用
        if '/api/devices' not in request.path:
            return jsonify(sensor_list)
        
        return jsonify({
            'success': True,
            'data': sensor_list
        })
        
    except Exception as e:
        logging.error(f"Failed to get sensors for device {device_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@device_bp.route('/api/devices/<int:device_id>/sensors', methods=['POST'])
def create_device_sensor(device_id):
    """为设备创建传感器"""
    try:
        data = request.get_json()
        
        # 验证必要字段
        required_fields = ['name', 'sensor_type', 'data_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        if not HAS_SERVICES:
            # Mock 模式
            new_sensor = {
                'id': max([s['id'] for s in MOCK_SENSORS]) + 1,
                'device_id': device_id,
                'name': data['name'],
                'sensor_type': data['sensor_type'],
                'type': data['sensor_type'],  # 兼容性
                'data_type': data['data_type'],
                'unit': data.get('unit'),
                'status': 'active',
                'created_at': datetime.utcnow().isoformat()
            }
            MOCK_SENSORS.append(new_sensor)
            return jsonify({'success': True, 'data': new_sensor}), 201
        
        sensor = SensorService.create_sensor(
            device_id=device_id,
            name=data['name'],
            sensor_type=data['sensor_type'],
            data_type=data['data_type'],
            unit=data.get('unit'),
            description=data.get('description'),
            config=data.get('config', {})
        )
        
        return jsonify({
            'success': True,
            'data': sensor.to_dict()
        }), 201
        
    except Exception as e:
        logging.error(f"Failed to create sensor for device {device_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== 读数管理 API ====================

@device_bp.route('/api/devices/<int:device_id>/readings', methods=['GET'])
def get_device_readings(device_id):
    """获取设备的读数"""
    try:
        # 获取查询参数
        sensor_id = request.args.get('sensor_id', type=int)
        data_type = request.args.get('data_type')
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # 时间范围
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        
        if start_time:
            start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        if end_time:
            end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        
        if not HAS_SERVICES:
            # Mock 模式
            if sensor_id:
                readings = get_mock_readings(sensor_id, limit)
            else:
                # 获取设备所有传感器的读数
                device_sensors = [s for s in MOCK_SENSORS if s['device_id'] == device_id]
                readings = []
                sensors_to_query = device_sensors[:3]  # 限制传感器数量
                for sensor in sensors_to_query:
                    readings.extend(get_mock_readings(sensor['id'], limit // len(sensors_to_query) if sensors_to_query else limit))
                
            if data_type:
                readings = [r for r in readings if r.get('data_type') == data_type]
                
            return jsonify({'success': True, 'data': readings[offset:offset+limit], 'total': len(readings)})
        
        if sensor_id:
            readings = ReadingService.get_readings_by_sensor(sensor_id, limit, offset)
        elif data_type:
            readings = ReadingService.get_readings_by_type(data_type, device_id, limit, offset)
        elif start_time or end_time:
            readings = ReadingService.get_readings_in_timerange(
                device_id=device_id,
                start_time=start_time,
                end_time=end_time,
                limit=limit
            )
        else:
            readings = ReadingService.get_readings_by_device(device_id, limit, offset)
        
        return jsonify({
            'success': True,
            'data': [reading.to_dict() for reading in readings],
            'total': len(readings)
        })
        
    except Exception as e:
        logging.error(f"Failed to get readings for device {device_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@device_bp.route('/api/devices/<int:device_id>/sensors/<int:sensor_id>/readings', methods=['POST'])
def create_sensor_reading(device_id, sensor_id):
    """为传感器创建读数"""
    try:
        # 检查是否为文件上传
        if 'file' in request.files:
            # 多媒体文件上传
            file = request.files['file']
            if file.filename == '':
                return jsonify({'success': False, 'error': 'No file selected'}), 400
            
            # 获取文件信息
            filename = file.filename or ''
            file_format = filename.split('.')[-1].lower() if '.' in filename else ''
            data_type = request.form.get('data_type', 'image')
            
            if data_type not in ['image', 'video']:
                return jsonify({'success': False, 'error': 'Invalid data type for file upload'}), 400
            
            # 元数据
            metadata = {}
            metadata_str = request.form.get('metadata')
            if metadata_str:
                import json
                try:
                    metadata = json.loads(metadata_str)
                except json.JSONDecodeError:
                    metadata = {}
            
            if not HAS_SERVICES:
                # Mock 模式
                reading = {
                    'id': 999,
                    'sensor_id': sensor_id,
                    'device_id': device_id,
                    'data_type': data_type,
                    'file_path': f'/mock/uploads/{filename}',
                    'file_format': file_format,
                    'file_size': 100000,  # Mock
                    'timestamp': datetime.utcnow().isoformat(),
                    'metadata': metadata
                }
                return jsonify({'success': True, 'data': reading}), 201
            
            if HAS_SERVICES and ReadingService:  # type: ignore
                reading = ReadingService.create_multimedia_reading(  # type: ignore
                    sensor_id=sensor_id,
                    file_data=file.stream,  # type: ignore
                    data_type=data_type,
                    file_format=file_format,
                    metadata=metadata
                )
                
                return jsonify({
                    'success': True,
                    'data': reading.to_dict()  # type: ignore
                }), 201
            
            return jsonify({'success': False, 'error': 'Service not available'}), 503
            
        else:
            # 数值型数据
            data = request.get_json()
            
            if 'value' not in data:
                return jsonify({'success': False, 'error': 'Missing required field: value'}), 400
            
            timestamp = None
            if data.get('timestamp'):
                timestamp = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
            
            if not HAS_SERVICES:
                # Mock 模式
                reading = {
                    'id': 998,
                    'sensor_id': sensor_id,
                    'device_id': device_id,
                    'data_type': 'numeric',
                    'numeric_value': data['value'],
                    'value': data['value'],  # 兼容性
                    'timestamp': (timestamp or datetime.utcnow()).isoformat(),
                    'metadata': data.get('metadata', {})
                }
                return jsonify({'success': True, 'data': reading}), 201
            
            reading = ReadingService.create_numeric_reading(
                sensor_id=sensor_id,
                value=data['value'],
                timestamp=timestamp,
                metadata=data.get('metadata', {})
            )
            
            return jsonify({
                'success': True,
                'data': reading.to_dict()
            }), 201
        
    except Exception as e:
        logging.error(f"Failed to create reading for sensor {sensor_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== 文件下载 API ====================

@device_bp.route('/api/devices/readings/<int:reading_id>/download', methods=['GET'])
def download_reading_file(reading_id):
    """下载读数关联的文件"""
    try:
        if not HAS_SERVICES:
            return jsonify({'success': False, 'error': 'File download not available in mock mode'}), 501
        
        reading = ReadingService.get_reading_by_id(reading_id)
        if not reading or not reading.is_multimedia:
            return jsonify({'success': False, 'error': 'Reading not found or not a multimedia file'}), 404
        
        # 尝试从存储服务下载文件
        if reading.bucket_name and reading.object_key:
            file_stream = storage_service.download_file(reading.bucket_name, reading.object_key)
            if file_stream:
                return send_file(
                    file_stream,
                    as_attachment=True,
                    download_name=f"{reading.object_key}",
                    mimetype='application/octet-stream'
                )
        
        # 尝试从本地文件
        if reading.file_path and os.path.exists(reading.file_path):
            return send_file(reading.file_path, as_attachment=True)
        
        return jsonify({'success': False, 'error': 'File not found'}), 404
        
    except Exception as e:
        logging.error(f"Failed to download file for reading {reading_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== 统计和分析 API ====================

@device_bp.route('/api/devices/<int:device_id>/statistics', methods=['GET'])
def get_device_statistics(device_id):
    """获取设备统计信息"""
    try:
        days = request.args.get('days', 7, type=int)
        
        if not HAS_SERVICES:
            # Mock 统计数据
            stats = {
                'device_id': device_id,
                'total_readings': 1000,
                'readings_by_type': {
                    'numeric': 800,
                    'image': 150,
                    'video': 50
                },
                'sensors_count': len([s for s in MOCK_SENSORS if s['device_id'] == device_id]),
                'time_range_days': days
            }
            return jsonify({'success': True, 'data': stats})
        
        summary = DeviceService.get_device_readings_summary(device_id, days)
        
        return jsonify({'success': True, 'data': summary})
        
    except Exception as e:
        logging.error(f"Failed to get statistics for device {device_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@device_bp.route('/api/devices/<int:device_id>/health', methods=['GET'])
def get_device_health(device_id):
    """获取设备健康状态"""
    try:
        if not HAS_SERVICES:
            # Mock 健康状态
            device = next((d for d in MOCK_DEVICES if d['id'] == device_id), None)
            if not device:
                return jsonify({'success': False, 'error': 'Device not found'}), 404
                
            health = {
                'status': 'healthy' if device.get('status') == 'online' else 'warning',
                'message': 'Device is operating normally' if device.get('status') == 'online' else 'Device is offline',
                'last_check': datetime.utcnow().isoformat(),
                'device_status': device.get('status')
            }
            return jsonify({'success': True, 'data': health})
        
        health = DeviceService.get_device_health_status(device_id)
        
        return jsonify({'success': True, 'data': health})
        
    except Exception as e:
        logging.error(f"Failed to get health status for device {device_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== 传感器统计 API (合并版本) ====================

@device_bp.route('/api/devices/<int:device_id>/sensors/<int:sensor_id>/stats', methods=['GET'])
@device_bp.route('/sensors/<int:sensor_id>/stats', methods=['GET'])
def get_sensor_stats(sensor_id, device_id=None):
    """获取传感器统计信息 - 支持新旧版本"""
    try:
        days = request.args.get('days', 1, type=int)  # 默认1天
        hours = days * 24
        
        if not HAS_SERVICES and (os.getenv('ALLOW_NO_DB', '').lower() == 'true' or not HAS_DB_MODELS):
            mock_readings = get_mock_readings(sensor_id, hours * 6, hours)  # 每10分钟一个数据点
            if not mock_readings:
                return jsonify({'error': 'No data available'}), 404
            
            # 提取数值数据
            values = []
            for r in mock_readings:
                value = r.get('value') or r.get('numeric_value')
                if value is not None:
                    values.append(value)
            
            if not values:
                return jsonify({'error': 'No numeric data available'}), 404
            
            sensor = next((s for s in MOCK_SENSORS if s['id'] == sensor_id), None)
            
            stats = {
                'sensor_id': sensor_id,
                'type': sensor.get('type') or sensor.get('sensor_type', 'value') if sensor else 'value',
                'min': min(values),
                'max': max(values),
                'avg': round(sum(values) / len(values), 2),
                'count': len(values),
                'time_range_days': days
            }
            
            # 根据API版本返回不同格式
            if '/api/devices' in request.path:
                return jsonify({'success': True, 'data': stats})
            else:
                return jsonify(stats)
        
        # 使用数据库或服务层
        if HAS_SERVICES:
            # 使用服务层获取统计信息
            stats = SensorService.get_sensor_statistics(sensor_id, days)
            if not stats:
                return jsonify({'success': False, 'error': 'No data available'}), 404
            return jsonify({'success': True, 'data': stats})
        
        elif HAS_DB_MODELS:
            # 直接使用数据库模型
            time_filter = datetime.utcnow() - timedelta(days=days)
            readings = Reading.query.filter(
                Reading.sensor_id == sensor_id,
                Reading.timestamp >= time_filter
            ).all()
            
            if not readings:
                return jsonify({'error': 'No data available'}), 404
            
            values = [r.value for r in readings if r.value is not None]
            if not values:
                return jsonify({'error': 'No numeric data available'}), 404
                
            stats = {
                'sensor_id': sensor_id,
                'min': min(values),
                'max': max(values),
                'avg': round(sum(values) / len(values), 2),
                'count': len(values),
                'time_range_days': days
            }
            
            # 根据API版本返回不同格式
            if '/api/devices' in request.path:
                return jsonify({'success': True, 'data': stats})
            else:
                return jsonify(stats)
        
        return jsonify({'error': 'No data source available'}), 500
        
    except Exception as e:
        logging.error(f"Failed to get sensor stats for sensor {sensor_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
