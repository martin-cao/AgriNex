from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required
from models.sensor import Sensor
from models.prediction import Prediction
from services.forecast_service import ForecastService
from extensions import db
import threading
import logging

logger = logging.getLogger(__name__)

forecast_bp = Blueprint('forecast', __name__, url_prefix='/api/forecasts')

@forecast_bp.route('/sensors/<int:sensor_id>', methods=['POST'])
@jwt_required()
def trigger_forecast(sensor_id):
    """手动触发预测 - 异步执行"""
    sensor = Sensor.query.get_or_404(sensor_id)
    
    # 获取请求参数
    data = request.get_json() or {}
    field = data.get('field', 'numeric_value')
    period = data.get('period', '24h')
    
    # 验证预测周期
    if not ForecastService.validate_forecast_period(period):
        return jsonify({
            'success': False,
            'error': f'不支持的预测周期: {period}',
            'available_periods': ForecastService.get_forecast_options()
        }), 400
    
    try:
        # 在主线程中获取Flask应用实例和必要参数，避免context问题
        from flask import copy_current_request_context
        
        @copy_current_request_context
        def run_forecast_task():
            """在后台线程中运行预测任务"""
            try:
                logger.info("开始后台预测任务 - 传感器: %s, 周期: %s", sensor_id, period)
                result, error = ForecastService.predict(sensor_id, field, period)
                
                if error:
                    logger.error("预测失败 - 传感器: %s, 错误: %s", sensor_id, error)
                    return
                
                if result:
                    # 保存预测结果到数据库
                    ForecastService.save_predictions(sensor_id, field, result)
                    logger.info("预测完成并保存 - 传感器: %s, 预测点数: %s", sensor_id, len(result))
                else:
                    logger.warning("预测结果为空 - 传感器: %s", sensor_id)
                    
            except Exception as e:
                logger.error("后台预测任务异常 - 传感器: %s, 错误: %s", sensor_id, str(e))
        
        # 在后台线程中运行预测任务
        thread = threading.Thread(target=run_forecast_task)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': f'预测任务已提交，预测周期: {period}',
            'sensor_id': sensor_id,
            'field': field,
            'period': period,
            'status': 'processing'
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

@forecast_bp.route('/options', methods=['GET'])
def get_forecast_options():
    """获取可用的预测时长选项"""
    return jsonify({
        'success': True,
        'periods': ForecastService.get_forecast_options(),
        'period_configs': {
            key: {
                'description': _get_period_description(key),
                'periods': config['periods'],
                'frequency': config['freq']
            }
            for key, config in ForecastService.FORECAST_PERIODS.items()
        }
    })

def _get_period_description(period_key):
    """获取预测周期的中文描述"""
    descriptions = {
        '30min': '未来30分钟（每分钟一个预测点）',
        '1h': '未来1小时（每分钟一个预测点）',
        '2h': '未来2小时（每5分钟一个预测点）',
        '6h': '未来6小时（每10分钟一个预测点）',
        '12h': '未来12小时（每15分钟一个预测点）',
        '24h': '未来24小时（每30分钟一个预测点）',
        '2d': '未来2天（每小时一个预测点）',
        '5d': '未来5天（每2小时一个预测点）',
        '7d': '未来7天（每2小时一个预测点）'
    }
    return descriptions.get(period_key, period_key)

@forecast_bp.route('/fields', methods=['GET'])
def get_fields():
    """获取可预测的字段列表"""
    fields = ForecastService.get_numeric_fields()
    return jsonify({'fields': fields})

@forecast_bp.route('/<int:device_id>', methods=['GET'])
def predict(device_id):
    """
    设备预测接口（聚合设备下所有传感器数据）
    参数:
      - field: 要预测的字段（如 numeric_value）
      - period: 预测周期（如 '24h', '2d', '7d'）
    """
    field = request.args.get('field', 'numeric_value')
    period = request.args.get('period', '24h')
    
    if field not in ForecastService.get_numeric_fields():
        return jsonify({'error': f'字段 {field} 不可预测'}), 400
    
    if not ForecastService.validate_forecast_period(period):
        return jsonify({
            'error': f'不支持的预测周期: {period}',
            'available_periods': ForecastService.get_forecast_options()
        }), 400
    
    # 使用设备级别的预测方法
    result, err = ForecastService.predict_by_device(device_id, field, period)
    if err:
        return jsonify({'error': err}), 400
    
    # 可选：保存预测结果到第一个传感器（如果需要的话）
    # TODO: 考虑是否需要为设备级别预测创建特殊的保存逻辑
    
    return jsonify({
        'device_id': device_id,
        'field': field,
        'period': period,
        'period_description': _get_period_description(period),
        'forecast': result,
        'forecast_count': len(result) if result else 0
    })

@forecast_bp.route('/history', methods=['GET'])
@jwt_required()
def get_prediction_history():
    """获取所有预测历史记录"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 50, type=int), 100)
        
        # 使用原生SQL或者分步查询来获取预测记录和传感器信息
        predictions_query = Prediction.query.order_by(Prediction.generated_at.desc())
        pagination = predictions_query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        predictions = []
        for pred in pagination.items:
            # 查询对应的传感器信息
            sensor = Sensor.query.get(pred.sensor_id)
            if sensor:
                # 根据传感器类型生成中文描述
                sensor_type_desc = _get_sensor_type_description(sensor.type)
                
                predictions.append({
                    'id': pred.id,
                    'sensor_id': pred.sensor_id,
                    'sensor_name': sensor.name,
                    'sensor_type': sensor.type,
                    'sensor_type_desc': sensor_type_desc,
                    'unit': sensor.unit,
                    'metric_type': sensor_type_desc,  # 显示传感器类型而不是technical field
                    'predict_ts': pred.predict_ts.isoformat(),
                    'yhat': pred.yhat,
                    'yhat_lower': pred.yhat_lower,
                    'yhat_upper': pred.yhat_upper,
                    'generated_at': pred.generated_at.isoformat()
                })
            else:
                # 如果传感器不存在，使用原始数据
                predictions.append({
                    'id': pred.id,
                    'sensor_id': pred.sensor_id,
                    'sensor_name': f'传感器 {pred.sensor_id}',
                    'sensor_type': 'unknown',
                    'sensor_type_desc': '未知',
                    'unit': '',
                    'metric_type': pred.metric_type or '未知',
                    'predict_ts': pred.predict_ts.isoformat(),
                    'yhat': pred.yhat,
                    'yhat_lower': pred.yhat_lower,
                    'yhat_upper': pred.yhat_upper,
                    'generated_at': pred.generated_at.isoformat()
                })
        
        return jsonify({
            'success': True,
            'data': predictions,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages
            }
        })
        
    except Exception as e:
        logger.error("获取预测历史失败: %s", str(e))
        return jsonify({
            'success': False,
            'error': f'获取预测历史失败: {str(e)}'
        }), 500

def _get_sensor_type_description(sensor_type):
    """获取传感器类型的中文描述"""
    type_descriptions = {
        'temperature': '温度',
        'humidity': '湿度',
        'light': '光照强度',
        'soil_moisture': '土壤湿度',
        'soil_temperature': '土壤温度',
        'soil_ph': '土壤pH值',
        'soil_ec': '土壤电导率',
        'water_temperature': '水温',
        'dissolved_oxygen': '溶解氧',
        'water_ph': '水体pH值',
        'turbidity': '浊度',
        'co2': 'CO2浓度',
        'ammonia': '氨气浓度',
        'air_quality': '空气质量',
        'multispectral': '多光谱',
        'thermal': '热红外',
        'altitude': '高度',
        'gps_accuracy': 'GPS精度'
    }
    return type_descriptions.get(sensor_type, sensor_type)
