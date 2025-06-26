from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.models.sensor import Sensor
from backend.models.prediction import Prediction
from backend.services.forecast_service import ForecastService
from backend.extensions import db

forecast_bp = Blueprint('forecast', __name__, url_prefix='/api/forecast')

@forecast_bp.route('/sensors/<int:sensor_id>', methods=['POST'])
@jwt_required()
def trigger_forecast(sensor_id):
    """手动触发预测"""
    sensor = Sensor.query.get_or_404(sensor_id)
    
    try:
        # TODO: 实现异步预测任务
        # 目前返回占位响应
        return jsonify({
            'success': True,
            'message': 'Forecast task submitted',
            'sensor_id': sensor_id,
            'status': 'pending'
        }), 202
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@forecast_bp.route('/sensors/<int:sensor_id>', methods=['GET'])
@jwt_required()
def get_predictions(sensor_id):
    """获取传感器预测结果"""
    sensor = Sensor.query.get_or_404(sensor_id)
    
    # 分页参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    predictions = Prediction.query.filter_by(sensor_id=sensor_id)\
                            .order_by(Prediction.predict_ts.desc())\
                            .paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'success': True,
        'data': [pred.to_dict() for pred in predictions.items],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': predictions.total,
            'pages': predictions.pages
        }
    })

@forecast_bp.route('/sensors/<int:sensor_id>/latest', methods=['GET'])
@jwt_required()
def get_latest_predictions(sensor_id):
    """获取传感器最新预测结果"""
    sensor = Sensor.query.get_or_404(sensor_id)
    
    # 获取最新的预测结果（未来24小时）
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    future_24h = now + timedelta(hours=24)
    
    predictions = Prediction.query.filter_by(sensor_id=sensor_id)\
                            .filter(Prediction.predict_ts >= now)\
                            .filter(Prediction.predict_ts <= future_24h)\
                            .order_by(Prediction.predict_ts.asc())\
                            .all()
    
    if not predictions:
        return jsonify({
            'success': False,
            'message': 'No recent predictions found'
        }), 404
    
    return jsonify({
        'success': True,
        'data': [pred.to_dict() for pred in predictions],
        'forecast_period': {
            'start': now.isoformat(),
            'end': future_24h.isoformat(),
            'duration_hours': 24
        }
    })
