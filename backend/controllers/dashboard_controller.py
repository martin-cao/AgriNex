from flask import Blueprint, jsonify, current_app
from datetime import datetime
from flask_jwt_extended import jwt_required
from sqlalchemy import func

from models.device import Device
from models.sensor import Sensor
from models.alarm import Alarm
from models.reading import Reading
from extensions import db

# Blueprint for dashboard related endpoints
# Registered with url_prefix='/api/dashboard' in app.py

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_stats():
    """Return aggregated statistics for the dashboard"""
    try:
        devices_total = db.session.query(func.count(Device.id)).filter(Device.status != 'deleted').scalar()
        devices_online = db.session.query(func.count(Device.id)).filter(Device.status == 'active').scalar()
        devices_offline = db.session.query(func.count(Device.id)).filter(Device.status == 'offline').scalar()
        devices_error = db.session.query(func.count(Device.id)).filter(Device.status == 'error').scalar()

        sensors_total = db.session.query(func.count(Sensor.id)).filter(Sensor.status != 'deleted').scalar()
        sensors_active = db.session.query(func.count(Sensor.id)).filter(Sensor.status == 'active').scalar()
        sensors_inactive = db.session.query(func.count(Sensor.id)).filter(Sensor.status == 'inactive').scalar()
        sensors_error = db.session.query(func.count(Sensor.id)).filter(Sensor.status == 'error').scalar()

        alarms_total = db.session.query(func.count(Alarm.id)).scalar()
        alarms_active = db.session.query(func.count(Alarm.id)).filter(Alarm.status == 'active').scalar()
        alarms_resolved = db.session.query(func.count(Alarm.id)).filter(Alarm.status == 'resolved').scalar()
        alarms_critical = db.session.query(func.count(Alarm.id)).filter(Alarm.severity == 'high').scalar()

        data_points = db.session.query(func.count(Reading.id)).scalar()

        stats = {
            'devices': {
                'total': devices_total,
                'online': devices_online,
                'offline': devices_offline,
                'error': devices_error,
            },
            'sensors': {
                'total': sensors_total,
                'active': sensors_active,
                'inactive': sensors_inactive,
                'error': sensors_error,
            },
            'alarms': {
                'total': alarms_total,
                'active': alarms_active,
                'resolved': alarms_resolved,
                'critical': alarms_critical,
            },
            'data_points': data_points,
            'last_updated': datetime.utcnow().isoformat(),
        }

        return jsonify({'success': True, 'data': stats})
    except Exception as e:
        current_app.logger.error('Failed to gather dashboard stats: %s', e)
        return jsonify({'success': False, 'message': 'Failed to get stats'}), 500


@dashboard_bp.route('/system-health', methods=['GET'])
@jwt_required()
def get_system_health():
    """Return basic system health information"""
    status = {
        'cpu_usage': 0,
        'memory_usage': 0,
        'disk_usage': 0,
        'network_status': 'good',
        'database_status': 'unknown',
        'mqtt_status': 'unknown',
        'api_response_time': 0,
    }
    try:
        # database check
        db.session.execute(db.text('SELECT 1'))
        status['database_status'] = 'connected'
    except Exception as e:
        status['database_status'] = f'error: {e}'

    try:
        from services.mqtt_service import mqtt_service
        mqtt_info = mqtt_service.get_connection_status()
        status['mqtt_status'] = 'connected' if mqtt_info.get('connected') else 'disconnected'
    except Exception as e:
        status['mqtt_status'] = f'error: {e}'

    status['last_updated'] = datetime.utcnow().isoformat()
    return jsonify({'success': True, 'data': status})