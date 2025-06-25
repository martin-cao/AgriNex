from flask import Blueprint, request, jsonify
from models.device import Device
from models.sensor import Sensor
from models.reading import Reading
from extensions import db

mcp_bp = Blueprint('mcp', __name__, url_prefix='/api/v1/mcp')

# 添加设备
@mcp_bp.route('/add', methods=['POST'])
def add_device():
    data = request.get_json()
    new_device = Device(name=data['name'], location=data['location'], type=data.get('type'))
    db.session.add(new_device)
    db.session.commit()
    return jsonify({"message": "Device added successfully"}), 201

# 获取所有设备
@mcp_bp.route('/devices', methods=['GET'])
def get_devices():
    devices = Device.query.all()
    return jsonify([{
        'id': device.id,
        'name': device.name,
        'location': device.location,
        'type': device.type,
        'status': device.status
    } for device in devices])

# 添加传感器
@mcp_bp.route('/devices/<int:device_id>/sensors', methods=['POST'])
def add_sensor(device_id):
    data = request.get_json()
    new_sensor = Sensor(
        device_id=device_id,
        type=data['type'],
        name=data.get('name'),
        unit=data.get('unit'),
        status=data.get('status', 'active')
    )
    db.session.add(new_sensor)
    db.session.commit()
    return jsonify({"message": "Sensor added successfully"}), 201

# 获取设备下所有传感器
@mcp_bp.route('/devices/<int:device_id>/sensors', methods=['GET'])
def get_sensors(device_id):
    sensors = Sensor.query.filter_by(device_id=device_id).all()
    return jsonify([{
        'id': sensor.id,
        'type': sensor.type,
        'name': sensor.name,
        'unit': sensor.unit,
        'status': sensor.status
    } for sensor in sensors])

# 添加读数
@mcp_bp.route('/sensors/<int:sensor_id>/readings', methods=['POST'])
def add_reading(sensor_id):
    data = request.get_json()
    new_reading = Reading(
        sensor_id=sensor_id,
        timestamp=data.get('timestamp'),
        value=data['value']
    )
    db.session.add(new_reading)
    db.session.commit()
    return jsonify({"message": "Reading added successfully"}), 201

# 获取传感器所有读数
@mcp_bp.route('/sensors/<int:sensor_id>/readings', methods=['GET'])
def get_readings(sensor_id):
    readings = Reading.query.filter_by(sensor_id=sensor_id).all()
    return jsonify([{
        'timestamp': reading.timestamp.isoformat() if reading.timestamp else None,
        'value': reading.value
    } for reading in readings])
