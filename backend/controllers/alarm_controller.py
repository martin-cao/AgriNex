from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.models.alarm import Alarm
from backend.models.sensor import Sensor
from backend.services.alarm_service import AlarmService
from backend.extensions import db

alarm_bp = Blueprint('alarm', __name__, url_prefix='/api/alarms')

@alarm_bp.route('/', methods=['GET'])
@jwt_required()
def list_alarms():
    """获取告警列表"""
    # 查询参数
    status = request.args.get('status', 'active')  # active/resolved/all
    severity = request.args.get('severity')  # low/medium/high
    sensor_id = request.args.get('sensor_id', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    query = Alarm.query
    
    if status != 'all':
        query = query.filter(Alarm.status == status)
    
    if severity:
        query = query.filter(Alarm.severity == severity)
    
    if sensor_id:
        query = query.filter(Alarm.sensor_id == sensor_id)
    
    alarms = query.order_by(Alarm.created_at.desc())\
                 .paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'success': True,
        'data': [alarm.to_dict() for alarm in alarms.items],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': alarms.total,
            'pages': alarms.pages
        }
    })

@alarm_bp.route('/<int:alarm_id>', methods=['GET'])
@jwt_required()
def get_alarm(alarm_id):
    """获取特定告警"""
    alarm = Alarm.query.get_or_404(alarm_id)
    return jsonify({
        'success': True,
        'data': alarm.to_dict()
    })

@alarm_bp.route('/<int:alarm_id>/resolve', methods=['PUT'])
@jwt_required()
def resolve_alarm(alarm_id):
    """解决告警"""
    alarm = Alarm.query.get_or_404(alarm_id)
    data = request.get_json() or {}
    
    try:
        resolved_by = data.get('resolved_by', 'system')
        alarm.resolve(resolved_by=resolved_by)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Alarm resolved successfully',
            'data': alarm.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@alarm_bp.route('/sensors/<int:sensor_id>', methods=['GET'])
@jwt_required()
def get_sensor_alarms(sensor_id):
    """获取特定传感器的告警"""
    sensor = Sensor.query.get_or_404(sensor_id)
    
    status = request.args.get('status', 'active')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    query = Alarm.query.filter_by(sensor_id=sensor_id)
    
    if status != 'all':
        query = query.filter(Alarm.status == status)
    
    alarms = query.order_by(Alarm.created_at.desc())\
                 .paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'success': True,
        'data': [alarm.to_dict() for alarm in alarms.items],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': alarms.total,
            'pages': alarms.pages
        }
    })

@alarm_bp.route('/statistics', methods=['GET'])
@jwt_required()
def get_alarm_statistics():
    """获取告警统计信息"""
    from sqlalchemy import func
    
    # 按状态统计
    status_stats = db.session.query(
        Alarm.status,
        func.count(Alarm.id).label('count')
    ).group_by(Alarm.status).all()
    
    # 按严重级别统计
    severity_stats = db.session.query(
        Alarm.severity,
        func.count(Alarm.id).label('count')
    ).group_by(Alarm.severity).all()
    
    # 按传感器统计
    sensor_stats = db.session.query(
        Alarm.sensor_id,
        func.count(Alarm.id).label('count')
    ).group_by(Alarm.sensor_id)\
     .order_by(func.count(Alarm.id).desc())\
     .limit(10).all()
    
    return jsonify({
        'success': True,
        'data': {
            'by_status': dict(status_stats),
            'by_severity': dict(severity_stats),
            'top_sensors': dict(sensor_stats)
        }
    })
