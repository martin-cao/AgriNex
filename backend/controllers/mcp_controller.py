from flask import Blueprint, request, jsonify
from models.sensor import Sensor
from models.reading import Reading
from extensions import db

mcp_bp = Blueprint('mcp', __name__, url_prefix='/api/v1/mcp')

# 添加传感器
@mcp_bp.route('/add', methods=['POST'])
def add_sensor():
    data = request.get_json()
    new_sensor = Sensor(name=data['name'], location=data['location'], unit=data['unit'])
    db.session.add(new_sensor)
    db.session.commit()
    return jsonify({"message": "Sensor added successfully"}), 201

# 获取所有传感器
@mcp_bp.route('/sensors', methods=['GET'])
def get_sensors():
    sensors = Sensor.query.all()
    return jsonify([{
        'id': sensor.id,
        'name': sensor.name,
        'location': sensor.location,
        'unit': sensor.unit
    } for sensor in sensors])

# 添加读数
@mcp_bp.route('/add_reading', methods=['POST'])
def add_reading():
    data = request.get_json()
    new_reading = Reading(
        sensor_id=data['sensor_id'],
        temperature=data['temperature'],
        humidity=data['humidity'],
        light=data['light']
    )
    db.session.add(new_reading)
    db.session.commit()
    return jsonify({"message": "Reading added successfully"}), 201

# 获取某个传感器的所有读数
@mcp_bp.route('/sensors/<int:sensor_id>/readings', methods=['GET'])
def get_readings(sensor_id):
    readings = Reading.query.filter_by(sensor_id=sensor_id).all()
    return jsonify([{
        'timestamp': reading.timestamp,
        'temperature': reading.temperature,
        'humidity': reading.humidity,
        'light': reading.light
    } for reading in readings])
