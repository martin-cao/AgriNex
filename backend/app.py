from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pymysql
from marshmallow import Schema, fields, ValidationError
from prophet import Prophet
import pandas as pd
import os

# 初始化数据库连接
pymysql.install_as_MySQLdb()
load_dotenv()

# 初始化 Flask 应用
app = Flask(__name__)
CORS(app)

# 配置数据库连接
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL',
                                                  'mysql://root:password@localhost/agriot')  # 修改为你的数据库连接信息
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# 数据模型定义
class Device(db.Model):
    __tablename__ = 'devices'
    device_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(255))
    type = db.Column(db.String(50))
    status = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    readings = db.relationship('Reading', backref='device', lazy=True)


class Reading(db.Model):
    __tablename__ = 'readings'
    reading_id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.device_id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    temperature = db.Column(db.Float)
    humidity = db.Column(db.Float)
    light = db.Column(db.Float)

    device = db.relationship('Device', backref=db.backref('readings', lazy=True))


class Prediction(db.Model):
    __tablename__ = 'predictions'
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.device_id'), nullable=False)
    predict_ts = db.Column(db.DateTime, default=datetime.utcnow)
    yhat = db.Column(db.Float)
    yhat_lower = db.Column(db.Float)
    yhat_upper = db.Column(db.Float)

    device = db.relationship('Device', backref=db.backref('predictions', lazy=True))


# 数据验证 Schema
class ControlDeviceSchema(Schema):
    target = fields.Str(required=True)
    state = fields.Str(required=True)


# 基本路由
@app.route('/')
def hello():
    return jsonify({"message": "AgriNex API is running!"})


@app.route('/api/health')
def health():
    return jsonify({"status": "healthy"})

# 使用 before_request 代替 before_first_request
@app.before_request
def before_request_func():
    for rule in app.url_map.iter_rules():
        print(f"Route: {rule} -> {rule.endpoint}")


# 获取设备列表
@app.route('/api/devices', methods=['GET'])
def get_devices():
    devices = Device.query.all()
    return jsonify(
        [{'device_id': device.device_id, 'name': device.name, 'location': device.location} for device in devices])


# 获取设备最新读数
@app.route('/api/devices/<int:device_id>/readings/latest', methods=['GET'])
def get_latest_reading(device_id):
    reading = Reading.query.filter_by(device_id=device_id).order_by(Reading.timestamp.desc()).first()
    if reading:
        return jsonify({
            'device_id': device_id,
            'timestamp': reading.timestamp.isoformat(),
            'temperature': reading.temperature,
            'humidity': reading.humidity,
            'light': reading.light
        })
    return jsonify({'error': 'No data available'}), 404


# 获取设备历史读数，支持分页
@app.route('/api/devices/<int:device_id>/readings', methods=['GET'])
def get_readings(device_id):
    limit = request.args.get('limit', 100, type=int)
    page = request.args.get('page', 1, type=int)  # 当前页码
    readings = Reading.query.filter_by(device_id=device_id).order_by(Reading.timestamp.desc()).paginate(page, limit,
                                                                                                        False)
    return jsonify([{
        'timestamp': reading.timestamp.isoformat(),
        'temperature': reading.temperature,
        'humidity': reading.humidity,
        'light': reading.light
    } for reading in readings.items])


# 获取设备的统计信息
@app.route('/api/devices/<int:device_id>/stats', methods=['GET'])
def get_stats(device_id):
    readings = Reading.query.filter_by(device_id=device_id).all()
    if not readings:
        return jsonify({'error': 'No data available'}), 404

    temperatures = [reading.temperature for reading in readings]
    humidity = [reading.humidity for reading in readings]
    light = [reading.light for reading in readings]

    return jsonify({
        'device_id': device_id,
        'metrics': {
            'temperature': {
                'min': min(temperatures),
                'max': max(temperatures),
                'avg': sum(temperatures) / len(temperatures)
            },
            'humidity': {
                'min': min(humidity),
                'max': max(humidity),
                'avg': sum(humidity) / len(humidity)
            },
            'light': {
                'min': min(light),
                'max': max(light),
                'avg': sum(light) / len(light)
            }
        }
    })


# 获取设备的预测数据
@app.route('/api/devices/<int:device_id>/predict', methods=['GET'])
def get_prediction(device_id):
    # 获取历史数据
    readings = Reading.query.filter_by(device_id=device_id).order_by(Reading.timestamp.desc()).limit(100).all()
    df = pd.DataFrame([{
        'ds': reading.timestamp,
        'y': reading.temperature  # 假设进行温度预测
    } for reading in readings])

    # 使用 Prophet 进行预测
    model = Prophet()
    model.fit(df)
    future = model.make_future_dataframe(df, periods=10, freq='H')
    forecast = model.predict(future)

    prediction_data = [
        {'timestamp': forecast['ds'][i], 'temperature': forecast['yhat'][i], 'humidity': forecast['yhat_lower'][i]}
        for i in range(len(forecast))
    ]
    return jsonify({
        'device_id': device_id,
        'forecast': prediction_data
    })


# 控制设备开关
@app.route('/api/devices/<int:device_id>/control', methods=['POST'])
def control_device(device_id):
    data = request.get_json()
    # 数据验证
    try:
        validated_data = ControlDeviceSchema().load(data)
    except ValidationError as err:
        return jsonify(err.messages), 400

    target = validated_data['target']
    state = validated_data['state']

    # 假设控制成功，返回成功信息
    return jsonify({
        'device_id': device_id,
        'target': target,
        'state': state,
        'status': 'success'
    })


# 启动 Flask 应用
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
