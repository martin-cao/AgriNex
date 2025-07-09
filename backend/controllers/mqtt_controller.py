# backend/controllers/mqtt_controller.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from backend.services.mqtt_service import mqtt_service

mqtt_bp = Blueprint('mqtt', __name__)


@mqtt_bp.route('/status', methods=['GET'])
@jwt_required()
def get_mqtt_status():
    """获取MQTT连接状态"""
    try:
        status = mqtt_service.get_connection_status()
        return jsonify({
            'success': True,
            'data': status
        })
    except Exception as e:
        current_app.logger.error("获取MQTT状态失败: %s", e)
        return jsonify({
            'success': False,
            'message': '获取MQTT状态失败'
        }), 500


@mqtt_bp.route('/sensors/<client_id>/config', methods=['POST'])
@jwt_required()
def send_sensor_config(client_id):
    """发送传感器配置"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': '配置数据不能为空'
            }), 400
        
        result = mqtt_service.send_sensor_config(client_id, data)
        
        if result:
            return jsonify({
                'success': True,
                'message': '配置发送成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '配置发送失败'
            }), 500
            
    except Exception as e:
        current_app.logger.error("发送传感器配置失败: %s", e)
        return jsonify({
            'success': False,
            'message': '发送传感器配置失败'
        }), 500


@mqtt_bp.route('/sensors/<client_id>/capture', methods=['POST'])
@jwt_required()
def trigger_capture(client_id):
    """触发数据捕获"""
    try:
        data = request.get_json() or {}
        capture_type = data.get('type', 'image')
        
        if capture_type not in ['image', 'video']:
            return jsonify({
                'success': False,
                'message': '无效的捕获类型'
            }), 400
        
        result = mqtt_service.send_capture_command(client_id, capture_type)
        
        if result:
            return jsonify({
                'success': True,
                'message': f'{capture_type}捕获命令发送成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': f'{capture_type}捕获命令发送失败'
            }), 500
            
    except Exception as e:
        current_app.logger.error("触发数据捕获失败: %s", e)
        return jsonify({
            'success': False,
            'message': '触发数据捕获失败'
        }), 500


@mqtt_bp.route('/publish', methods=['POST'])
@jwt_required()
def publish_message():
    """发布MQTT消息"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': '消息数据不能为空'
            }), 400
        
        topic = data.get('topic')
        payload = data.get('payload')
        qos = data.get('qos', 1)
        
        if not topic or not payload:
            return jsonify({
                'success': False,
                'message': '主题和负载不能为空'
            }), 400
        
        result = mqtt_service.publish(topic, payload, qos)
        
        if result:
            return jsonify({
                'success': True,
                'message': '消息发布成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '消息发布失败'
            }), 500
            
    except Exception as e:
        current_app.logger.error("发布MQTT消息失败: %s", e)
        return jsonify({
            'success': False,
            'message': '发布MQTT消息失败'
        }), 500
