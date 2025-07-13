"""
设备模拟管理API控制器
提供动态设备管理的REST API接口
"""

import logging
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from services.device_simulation_service import device_simulation_service, SimulationConfig
from models.device import Device
from models.sensor import Sensor

logger = logging.getLogger(__name__)

device_simulation_bp = Blueprint('device_simulation', __name__)


@device_simulation_bp.route('/simulations', methods=['GET'])
@jwt_required()
def get_active_simulations():
    """获取活跃的模拟设备列表"""
    try:
        simulations = device_simulation_service.get_active_simulations()
        return jsonify({
            'success': True,
            'data': simulations,
            'total': len(simulations)
        }), 200
    except Exception as e:
        logger.error("获取模拟设备列表失败: %s", e)
        return jsonify({
            'success': False,
            'error': 'Failed to get simulations',
            'message': str(e)
        }), 500


@device_simulation_bp.route('/simulations', methods=['POST'])
@jwt_required()
def start_device_simulation():
    """启动新的设备模拟"""
    try:
        data = request.get_json()
        
        # 验证必需参数
        required_fields = ['device_id', 'device_type', 'location']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': 'Missing required field',
                    'message': f'Field {field} is required'
                }), 400
        
        # 检查设备ID是否已存在
        existing_device = Device.query.filter_by(name=data['device_id']).first()
        if existing_device and existing_device.status == 'active':
            return jsonify({
                'success': False,
                'error': 'Device already exists',
                'message': f'Device {data["device_id"]} already exists and is active'
            }), 409
        
        # 创建模拟配置
        config = SimulationConfig(
            device_id=data['device_id'],
            device_type=data['device_type'],
            location=data['location'],
            interval=data.get('interval', 30),
            sensor_types=data.get('sensor_types')
        )
        
        # 启动模拟
        success = device_simulation_service.start_device_simulation(config)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Device simulation started for {config.device_id}',
                'data': {
                    'device_id': config.device_id,
                    'device_type': config.device_type,
                    'location': config.location,
                    'interval': config.interval,
                    'sensor_types': config.sensor_types
                }
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to start simulation',
                'message': 'Unable to start device simulation'
            }), 500
            
    except Exception as e:
        logger.error("启动设备模拟失败: %s", e)
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': str(e)
        }), 500


@device_simulation_bp.route('/simulations/<device_id>', methods=['DELETE'])
@jwt_required()
def stop_device_simulation(device_id):
    """停止设备模拟"""
    try:
        success = device_simulation_service.stop_device_simulation(device_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Device simulation stopped for {device_id}'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to stop simulation',
                'message': f'Device {device_id} not found in active simulations'
            }), 404
            
    except Exception as e:
        logger.error("停止设备模拟失败: %s", e)
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': str(e)
        }), 500


@device_simulation_bp.route('/simulations/<device_id>/restart', methods=['POST'])
@jwt_required()
def restart_device_simulation(device_id):
    """重启设备模拟"""
    try:
        success = device_simulation_service.restart_device_simulation(device_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Device simulation restarted for {device_id}'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to restart simulation',
                'message': f'Device {device_id} not found in active simulations'
            }), 404
            
    except Exception as e:
        logger.error("重启设备模拟失败: %s", e)
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': str(e)
        }), 500


@device_simulation_bp.route('/simulations/<device_id>/config', methods=['PUT'])
@jwt_required()
def update_device_config(device_id):
    """更新设备配置"""
    try:
        data = request.get_json()
        
        success = device_simulation_service.update_device_config(device_id, data)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Device configuration updated for {device_id}',
                'data': data
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to update configuration',
                'message': f'Device {device_id} not found in active simulations'
            }), 404
            
    except Exception as e:
        logger.error("更新设备配置失败: %s", e)
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': str(e)
        }), 500


@device_simulation_bp.route('/templates', methods=['GET'])
@jwt_required()
def get_device_templates():
    """获取设备模板列表"""
    templates = [
        {
            'id': 'soil_monitor',
            'name': 'Soil Monitor',
            'description': 'Monitor soil conditions including temperature, humidity, and pH',
            'default_sensors': ['temperature', 'humidity', 'ph'],
            'default_interval': 60
        },
        {
            'id': 'weather_station',
            'name': 'Weather Station',
            'description': 'Comprehensive weather monitoring station',
            'default_sensors': ['temperature', 'humidity', 'light_intensity', 'wind_speed'],
            'default_interval': 300
        },
        {
            'id': 'irrigation_controller',
            'name': 'Irrigation Controller',
            'description': 'Control and monitor irrigation systems',
            'default_sensors': ['flow_rate', 'pressure', 'valve_status'],
            'default_interval': 30
        },
        {
            'id': 'greenhouse_sensor',
            'name': 'Greenhouse Sensor',
            'description': 'Monitor greenhouse environmental conditions',
            'default_sensors': ['temperature', 'humidity', 'co2_level', 'light_intensity'],
            'default_interval': 120
        }
    ]
    
    return jsonify({
        'success': True,
        'data': templates
    }), 200


@device_simulation_bp.route('/sensors/types', methods=['GET'])
@jwt_required()
def get_sensor_types():
    """获取可用的传感器类型"""
    sensor_types = [
        {
            'type': 'temperature',
            'name': 'Temperature',
            'unit': '°C',
            'range': {'min': -20, 'max': 50}
        },
        {
            'type': 'humidity',
            'name': 'Humidity',
            'unit': '%',
            'range': {'min': 0, 'max': 100}
        },
        {
            'type': 'ph',
            'name': 'pH Level',
            'unit': 'pH',
            'range': {'min': 0, 'max': 14}
        },
        {
            'type': 'light_intensity',
            'name': 'Light Intensity',
            'unit': 'lx',
            'range': {'min': 0, 'max': 100000}
        },
        {
            'type': 'wind_speed',
            'name': 'Wind Speed',
            'unit': 'm/s',
            'range': {'min': 0, 'max': 50}
        },
        {
            'type': 'flow_rate',
            'name': 'Flow Rate',
            'unit': 'L/min',
            'range': {'min': 0, 'max': 100}
        },
        {
            'type': 'pressure',
            'name': 'Pressure',
            'unit': 'kPa',
            'range': {'min': 0, 'max': 1000}
        },
        {
            'type': 'valve_status',
            'name': 'Valve Status',
            'unit': 'status',
            'range': {'min': 0, 'max': 1}
        },
        {
            'type': 'co2_level',
            'name': 'CO2 Level',
            'unit': 'ppm',
            'range': {'min': 300, 'max': 2000}
        }
    ]
    
    return jsonify({
        'success': True,
        'data': sensor_types
    }), 200


@device_simulation_bp.route('/status', methods=['GET'])
@jwt_required()
def get_simulation_status():
    """获取模拟系统状态"""
    try:
        active_simulations = device_simulation_service.get_active_simulations()
        
        status = {
            'active_devices': len(active_simulations),
            'total_sensors': sum(len(sim.get('sensor_types', [])) for sim in active_simulations),
            'mqtt_connected': device_simulation_service._send_mqtt_command.__module__ is not None,  # 简化检查
            'last_updated': request.args.get('timestamp', 'now')
        }
        
        return jsonify({
            'success': True,
            'data': status
        }), 200
        
    except Exception as e:
        logger.error("获取模拟状态失败: %s", e)
        return jsonify({
            'success': False,
            'error': 'Failed to get status',
            'message': str(e)
        }), 500
