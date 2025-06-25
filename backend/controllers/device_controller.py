from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import random
import math
import os

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
    print("Warning: Database models not available, using mock data")

device_bp = Blueprint('device', __name__)

# Mock data for development mode
MOCK_DEVICES = [
    {"id": 1, "name": "温室1", "type": "greenhouse", "location": "温室1", "status": "online"},
    {"id": 2, "name": "温室2", "type": "greenhouse", "location": "温室2", "status": "offline"}
]
MOCK_SENSORS = [
    {"id": 1, "device_id": 1, "type": "temperature", "name": "温度传感器", "unit": "°C", "status": "active"},
    {"id": 2, "device_id": 1, "type": "humidity", "name": "湿度传感器", "unit": "%", "status": "active"},
    {"id": 3, "device_id": 2, "type": "light", "name": "光照传感器", "unit": "lux", "status": "active"}
]

def generate_mock_readings(sensor_id, hours=24):
    readings = []
    now = datetime.utcnow()
    sensor = next((s for s in MOCK_SENSORS if s['id'] == sensor_id), None)
    for i in range(hours * 6):
        timestamp = now - timedelta(minutes=i * 10)
        if not sensor:
            continue
        if sensor['type'] == 'temperature':
            value = 20 + 10 * random.random() + 3 * math.sin(i * 0.1)
        elif sensor['type'] == 'humidity':
            value = 40 + 30 * random.random() + 10 * math.sin(i * 0.05)
        elif sensor['type'] == 'light':
            hour_of_day = timestamp.hour
            if 6 <= hour_of_day <= 18:
                value = 500 + 1000 * random.random()
            else:
                value = 0 + 50 * random.random()
        else:
            value = random.random() * 100
        readings.append({
            "id": len(readings) + 1,
            "sensor_id": sensor_id,
            "timestamp": timestamp.isoformat(),
            "value": round(value, 2)
        })
    return readings[::-1]

# 获取设备列表
@device_bp.route('/devices', methods=['GET'])
def get_devices():
    if os.getenv('ALLOW_NO_DB', '').lower() == 'true' or not HAS_DB_MODELS:
        return jsonify({"devices": MOCK_DEVICES, "total": len(MOCK_DEVICES)})
    devices = Device.query.all()
    return jsonify([d.to_dict() for d in devices])

# 获取设备下所有传感器
@device_bp.route('/devices/<int:device_id>/sensors', methods=['GET'])
def get_sensors(device_id):
    if os.getenv('ALLOW_NO_DB', '').lower() == 'true' or not HAS_DB_MODELS:
        sensors = [s for s in MOCK_SENSORS if s['device_id'] == device_id]
        return jsonify(sensors)
    sensors = Sensor.query.filter_by(device_id=device_id).all()
    return jsonify([s.to_dict() for s in sensors])

# 获取传感器最新读数
@device_bp.route('/sensors/<int:sensor_id>/readings/latest', methods=['GET'])
def get_latest_reading(sensor_id):
    if os.getenv('ALLOW_NO_DB', '').lower() == 'true' or not HAS_DB_MODELS:
        mock_readings = generate_mock_readings(sensor_id, 1)
        if mock_readings:
            return jsonify(mock_readings[-1])
        return jsonify({'error': 'No data available'}), 404
    reading = Reading.query.filter_by(sensor_id=sensor_id).order_by(Reading.timestamp.desc()).first()
    if reading:
        return jsonify(reading.to_dict())
    return jsonify({'error': 'No data available'}), 404

# 获取传感器历史读数，支持分页
@device_bp.route('/sensors/<int:sensor_id>/readings', methods=['GET'])
def get_readings(sensor_id):
    limit = request.args.get('limit', 100, type=int)
    page = request.args.get('page', 1, type=int)
    if os.getenv('ALLOW_NO_DB', '').lower() == 'true' or not HAS_DB_MODELS:
        mock_readings = generate_mock_readings(sensor_id, 24)
        start = (page - 1) * limit
        end = start + limit
        paginated_readings = mock_readings[start:end]
        return jsonify(paginated_readings)
    readings = Reading.query.filter_by(sensor_id=sensor_id).order_by(Reading.timestamp.desc()).paginate(
        page=page, per_page=limit, error_out=False)
    return jsonify([r.to_dict() for r in readings.items])

# 获取传感器统计信息
@device_bp.route('/sensors/<int:sensor_id>/stats', methods=['GET'])
def get_sensor_stats(sensor_id):
    if os.getenv('ALLOW_NO_DB', '').lower() == 'true' or not HAS_DB_MODELS:
        mock_readings = generate_mock_readings(sensor_id, 24)
        if not mock_readings:
            return jsonify({'error': 'No data available'}), 404
        values = [r['value'] for r in mock_readings]
        sensor = next((s for s in MOCK_SENSORS if s['id'] == sensor_id), None)
        stats = {
            'sensor_id': sensor_id,
            'type': sensor['type'] if sensor else 'value',
            'min': min(values),
            'max': max(values),
            'avg': sum(values) / len(values),
            'count': len(values)
        }
        return jsonify(stats)
    readings = Reading.query.filter_by(sensor_id=sensor_id).all()
    if not readings:
        return jsonify({'error': 'No data available'}), 404
    values = [r.value for r in readings if r.value is not None]
    stats = {
        'sensor_id': sensor_id,
        'min': min(values),
        'max': max(values),
        'avg': sum(values) / len(values),
        'count': len(values)
    }
    return jsonify(stats)
