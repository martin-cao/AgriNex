# backend/controllers/device_controller.py
from flask import Blueprint, request, jsonify, send_file
from datetime import datetime, timedelta
from typing import Optional
import logging
import os

try:
    from backend.services.device_service import DeviceService
    from backend.services.sensor_service import SensorService
    from backend.services.reading_service import ReadingService
    from backend.services.storage_service import storage_service
    HAS_SERVICES = True
except ImportError:
    HAS_SERVICES = False
    logging.warning("Services not available, using mock mode")

device_bp = Blueprint('device', __name__, url_prefix='/api/devices')

# Mock data for development
MOCK_DEVICES = [
    {"id": 1, "name": "温室1", "device_type": "greenhouse", "location": "温室区域A", "status": "online"},
    {"id": 2, "name": "温室2", "device_type": "greenhouse", "location": "温室区域B", "status": "offline"}
]

MOCK_SENSORS = [
    {"id": 1, "device_id": 1, "name": "温度传感器", "sensor_type": "temperature", "data_type": "numeric", "unit": "°C", "status": "active"},
    {"id": 2, "device_id": 1, "name": "湿度传感器", "sensor_type": "humidity", "data_type": "numeric", "unit": "%", "status": "active"},
    {"id": 3, "device_id": 1, "name": "摄像头", "sensor_type": "camera", "data_type": "image", "unit": None, "status": "active"},
    {"id": 4, "device_id": 2, "name": "光照传感器", "sensor_type": "light", "data_type": "numeric", "unit": "lux", "status": "active"}
]

def get_mock_readings(sensor_id: int, limit: int = 100):
    """生成模拟读数数据"""
    import random
    import math
    
    readings = []
    sensor = next((s for s in MOCK_SENSORS if s['id'] == sensor_id), None)
    if not sensor:
        return []
    
    now = datetime.utcnow()
    for i in range(limit):
        timestamp = now - timedelta(minutes=i * 10)
        
        if sensor['data_type'] == 'numeric':
            if sensor['sensor_type'] == 'temperature':
                value = 20 + 10 * random.random() + 3 * math.sin(i * 0.1)
            elif sensor['sensor_type'] == 'humidity':
                value = 40 + 30 * random.random() + 10 * math.sin(i * 0.05)
            elif sensor['sensor_type'] == 'light':
                hour_of_day = timestamp.hour
                if 6 <= hour_of_day <= 18:
                    value = 500 + 1000 * random.random()
                else:
                    value = 0 + 50 * random.random()
            else:
                value = random.uniform(0, 100)
                
            readings.append({
                'id': i + 1,
                'sensor_id': sensor_id,
                'device_id': sensor['device_id'],
                'data_type': 'numeric',
                'numeric_value': round(value, 2),
                'timestamp': timestamp.isoformat(),
                'metadata': {}
            })
        else:
            # 模拟多媒体数据
            readings.append({
                'id': i + 1,
                'sensor_id': sensor_id,
                'device_id': sensor['device_id'],
                'data_type': sensor['data_type'],
                'file_path': f'/mock/images/device_{sensor["device_id"]}_sensor_{sensor_id}_{i}.jpg',
                'file_format': 'jpg',
                'file_size': random.randint(50000, 200000),
                'timestamp': timestamp.isoformat(),
                'metadata': {'width': 1920, 'height': 1080}
            })
    
    return readings

# ==================== 设备管理 API ====================

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
                devices = [d for d in devices if d.get('device_type') == device_type]
            if status:
                devices = [d for d in devices if d.get('status') == status]
            if search:
                devices = [d for d in devices if search.lower() in d.get('name', '').lower()]
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
        
        return jsonify({
            'success': True,
            'data': [device.to_dict() for device in devices],
            'total': len(devices)
        })
        
    except Exception as e:
        logging.error(f"Failed to get devices: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@device_bp.route('/<int:device_id>', methods=['GET'])
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

@device_bp.route('', methods=['POST'])
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

@device_bp.route('/<int:device_id>', methods=['PUT'])
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

@device_bp.route('/<int:device_id>', methods=['DELETE'])
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

@device_bp.route('/<int:device_id>/overview', methods=['GET'])
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
                    'numeric_sensors': len([s for s in sensors if s['data_type'] == 'numeric']),
                    'multimedia_sensors': len([s for s in sensors if s['data_type'] in ['image', 'video']])
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

@device_bp.route('/<int:device_id>/sensors', methods=['GET'])
def get_device_sensors(device_id):
    """获取设备的传感器列表"""
    try:
        data_type = request.args.get('data_type')
        
        if not HAS_SERVICES:
            # Mock 模式
            sensors = [s for s in MOCK_SENSORS if s['device_id'] == device_id]
            if data_type:
                sensors = [s for s in sensors if s['data_type'] == data_type]
            return jsonify({'success': True, 'data': sensors})
        
        if data_type:
            sensors = DeviceService.get_device_sensors_by_type(device_id, data_type)
        else:
            sensors = SensorService.get_sensors_by_device(device_id)
        
        return jsonify({
            'success': True,
            'data': [sensor.to_dict() for sensor in sensors]
        })
        
    except Exception as e:
        logging.error(f"Failed to get sensors for device {device_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@device_bp.route('/<int:device_id>/sensors', methods=['POST'])
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

@device_bp.route('/<int:device_id>/readings', methods=['GET'])
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
                for sensor in device_sensors[:3]:  # 限制传感器数量
                    readings.extend(get_mock_readings(sensor['id'], limit // len(device_sensors)))
                
            if data_type:
                readings = [r for r in readings if r['data_type'] == data_type]
                
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

@device_bp.route('/<int:device_id>/sensors/<int:sensor_id>/readings', methods=['POST'])
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
            file_format = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
            data_type = request.form.get('data_type', 'image')
            
            if data_type not in ['image', 'video']:
                return jsonify({'success': False, 'error': 'Invalid data type for file upload'}), 400
            
            # 元数据
            metadata = {}
            if request.form.get('metadata'):
                import json
                metadata = json.loads(request.form.get('metadata'))
            
            if not HAS_SERVICES:
                # Mock 模式
                reading = {
                    'id': 999,
                    'sensor_id': sensor_id,
                    'device_id': device_id,
                    'data_type': data_type,
                    'file_path': f'/mock/uploads/{file.filename}',
                    'file_format': file_format,
                    'file_size': 100000,  # Mock
                    'timestamp': datetime.utcnow().isoformat(),
                    'metadata': metadata
                }
                return jsonify({'success': True, 'data': reading}), 201
            
            reading = ReadingService.create_multimedia_reading(
                sensor_id=sensor_id,
                file_data=file.stream,
                data_type=data_type,
                file_format=file_format,
                metadata=metadata
            )
            
            return jsonify({
                'success': True,
                'data': reading.to_dict()
            }), 201
            
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

@device_bp.route('/readings/<int:reading_id>/download', methods=['GET'])
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

@device_bp.route('/<int:device_id>/statistics', methods=['GET'])
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
                'sensors_count': 3,
                'time_range_days': days
            }
            return jsonify({'success': True, 'data': stats})
        
        summary = DeviceService.get_device_readings_summary(device_id, days)
        
        return jsonify({'success': True, 'data': summary})
        
    except Exception as e:
        logging.error(f"Failed to get statistics for device {device_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@device_bp.route('/<int:device_id>/health', methods=['GET'])
def get_device_health(device_id):
    """获取设备健康状态"""
    try:
        if not HAS_SERVICES:
            # Mock 健康状态
            health = {
                'status': 'healthy',
                'message': 'Device is operating normally',
                'last_check': datetime.utcnow().isoformat()
            }
            return jsonify({'success': True, 'data': health})
        
        health = DeviceService.get_device_health_status(device_id)
        
        return jsonify({'success': True, 'data': health})
        
    except Exception as e:
        logging.error(f"Failed to get health status for device {device_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
