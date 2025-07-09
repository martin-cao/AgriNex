from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.alarm import Alarm
from models.alarm_rule import AlarmRule
from models.sensor import Sensor
from services.alarm_service import AlarmService
from services.alarm_monitor import alarm_monitor
from extensions import db
import logging

logger = logging.getLogger(__name__)
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

@alarm_bp.route('/<int:alarm_id>/resolve', methods=['POST'])
@jwt_required()
def resolve_alarm(alarm_id):
    """解决告警"""
    user_id = get_jwt_identity()
    alarm = AlarmService.resolve_alarm(alarm_id, user_id)
    
    if alarm:
        return jsonify({
            'success': True,
            'message': '告警已解决',
            'data': alarm.to_dict()
        })
    else:
        return jsonify({
            'success': False,
            'message': '告警不存在'
        }), 404

@alarm_bp.route('/rules', methods=['GET'])
@jwt_required()
def list_alarm_rules():
    """获取告警规则列表"""
    sensor_id = request.args.get('sensor_id', type=int)
    is_active = request.args.get('is_active', type=bool)
    
    rules = AlarmService.get_alarm_rules(sensor_id=sensor_id, is_active=is_active)
    
    return jsonify({
        'success': True,
        'data': [rule.to_dict() for rule in rules]
    })

@alarm_bp.route('/rules', methods=['POST'])
@jwt_required()
def create_alarm_rule():
    """创建告警规则"""
    data = request.get_json()
    
    # 验证必需字段
    required_fields = ['name', 'sensor_id', 'rule_type', 'condition', 'threshold_value']
    for field in required_fields:
        if field not in data:
            return jsonify({
                'success': False,
                'message': f'缺少必需字段: {field}'
            }), 400
    
    # 验证传感器是否存在
    sensor = Sensor.query.get(data['sensor_id'])
    if not sensor:
        return jsonify({
            'success': False,
            'message': '传感器不存在'
        }), 404
    
    # 验证条件操作符
    valid_conditions = ['>', '<', '>=', '<=', '==', '!=']
    if data['condition'] not in valid_conditions:
        return jsonify({
            'success': False,
            'message': f'无效的条件操作符，支持的操作符: {valid_conditions}'
        }), 400
    
    try:
        user_id = get_jwt_identity()
        rule = AlarmService.create_alarm_rule(
            name=data['name'],
            description=data.get('description', ''),
            sensor_id=data['sensor_id'],
            rule_type=data['rule_type'],
            condition=data['condition'],
            threshold_value=float(data['threshold_value']),
            consecutive_count=data.get('consecutive_count', 1),
            severity=data.get('severity', 'medium'),
            created_by=user_id,
            email_enabled=data.get('email_enabled', False),
            webhook_enabled=data.get('webhook_enabled', False),
            webhook_url=data.get('webhook_url')
        )
        
        return jsonify({
            'success': True,
            'message': '告警规则创建成功',
            'data': rule.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating alarm rule: {e}")
        return jsonify({
            'success': False,
            'message': '创建告警规则失败'
        }), 500

@alarm_bp.route('/rules/<int:rule_id>', methods=['GET'])
@jwt_required()
def get_alarm_rule(rule_id):
    """获取特定告警规则"""
    rule = AlarmRule.query.get_or_404(rule_id)
    return jsonify({
        'success': True,
        'data': rule.to_dict()
    })

@alarm_bp.route('/rules/<int:rule_id>', methods=['PUT'])
@jwt_required()
def update_alarm_rule(rule_id):
    """更新告警规则"""
    data = request.get_json()
    
    # 验证条件操作符（如果提供）
    if 'condition' in data:
        valid_conditions = ['>', '<', '>=', '<=', '==', '!=']
        if data['condition'] not in valid_conditions:
            return jsonify({
                'success': False,
                'message': f'无效的条件操作符，支持的操作符: {valid_conditions}'
            }), 400
    
    try:
        rule = AlarmService.update_alarm_rule(rule_id, **data)
        
        if rule:
            return jsonify({
                'success': True,
                'message': '告警规则更新成功',
                'data': rule.to_dict()
            })
        else:
            return jsonify({
                'success': False,
                'message': '告警规则不存在'
            }), 404
            
    except Exception as e:
        logger.error(f"Error updating alarm rule: {e}")
        return jsonify({
            'success': False,
            'message': '更新告警规则失败'
        }), 500

@alarm_bp.route('/rules/<int:rule_id>', methods=['DELETE'])
@jwt_required()
def delete_alarm_rule(rule_id):
    """删除告警规则"""
    try:
        success = AlarmService.delete_alarm_rule(rule_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': '告警规则删除成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '告警规则不存在'
            }), 404
            
    except Exception as e:
        logger.error(f"Error deleting alarm rule: {e}")
        return jsonify({
            'success': False,
            'message': '删除告警规则失败'
        }), 500

@alarm_bp.route('/rules/<int:rule_id>/toggle', methods=['POST'])
@jwt_required()
def toggle_alarm_rule(rule_id):
    """启用/禁用告警规则"""
    try:
        rule = AlarmRule.query.get_or_404(rule_id)
        rule.is_active = not rule.is_active
        db.session.commit()
        
        status = '启用' if rule.is_active else '禁用'
        return jsonify({
            'success': True,
            'message': f'告警规则已{status}',
            'data': rule.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error toggling alarm rule: {e}")
        return jsonify({
            'success': False,
            'message': '操作失败'
        }), 500

@alarm_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_alarm_stats():
    """获取告警统计信息"""
    sensor_id = request.args.get('sensor_id', type=int)
    days = request.args.get('days', 7, type=int)
    
    stats = AlarmService.get_alarm_statistics(sensor_id=sensor_id, days=days)
    
    return jsonify({
        'success': True,
        'data': stats
    })

@alarm_bp.route('/test/<int:sensor_id>', methods=['POST'])
@jwt_required()
def test_alarm_rules(sensor_id):
    """测试告警规则（用于调试）"""
    data = request.get_json()
    test_value = data.get('test_value')
    
    if test_value is None:
        return jsonify({
            'success': False,
            'message': '请提供测试值'
        }), 400
    
    try:
        # 立即检查告警
        triggered_alarms = alarm_monitor.check_reading_immediately(
            sensor_id=sensor_id,
            value=float(test_value)
        )
        
        return jsonify({
            'success': True,
            'message': f'测试完成，触发了 {len(triggered_alarms)} 个告警',
            'data': [alarm.to_dict() for alarm in triggered_alarms]
        })
        
    except Exception as e:
        logger.error(f"Error testing alarm rules: {e}")
        return jsonify({
            'success': False,
            'message': '测试失败'
        }), 500
    return jsonify({
        'success': True,
        'data': alarm.to_dict()
    })

@alarm_bp.route('/<int:alarm_id>/status', methods=['PUT'])
@jwt_required()
def resolve_alarm_put(alarm_id):
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
