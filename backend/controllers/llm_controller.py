# backend/controllers/llm_controller.py
"""
LLM控制器 - 提供智能农业建议和对话服务
"""
from flask import Blueprint, request, jsonify, Response, stream_template
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional, Any, Generator
import json

from models.sensor import Sensor
from models.reading import Reading
from models.device import Device
from models.alarm import Alarm
from services.llm_service import LLMService
from extensions import db

logger = logging.getLogger(__name__)
llm_bp = Blueprint('llm_assistant', __name__)

# 初始化LLM服务
llm_service = LLMService()

@llm_bp.route('/chat/stream', methods=['GET'])
def chat_stream():
    """
    流式聊天接口 - 使用Server-Sent Events，支持可选认证
    """
    try:
        # 尝试获取用户身份，支持URL参数和Header两种方式
        user_id = None
        try:
            # 首先尝试从URL参数获取token
            token = request.args.get('token')
            if token:
                from flask_jwt_extended import decode_token
                decoded_token = decode_token(token)
                user_id = decoded_token['sub']
            else:
                # 然后尝试从Header获取token
                from flask_jwt_extended import verify_jwt_in_request
                verify_jwt_in_request(optional=True)
                user_id = get_jwt_identity()
        except Exception as e:
            # 没有token也可以继续，但功能受限
            logger.debug("Token verification failed: %s", str(e))
            pass
            
        message = request.args.get('message')
        
        if not message:
            return jsonify({
                'success': False,
                'error': 'Message is required'
            }), 400
        
        def generate():
            try:
                # 获取传感器上下文
                sensor_context = _get_recent_sensor_context()
                
                # 生成流式响应
                full_response = ""
                for chunk in llm_service.generate_chat_response_stream(
                    message=message,
                    sensor_context=sensor_context
                ):
                    full_response += chunk
                    data = {
                        'type': 'chunk',
                        'content': chunk
                    }
                    yield f"data: {json.dumps(data)}\n\n"
                
                # 发送完成信号
                completion_data = {
                    'type': 'complete',
                    'confidence': 0.85  # 可以从LLM服务返回实际置信度
                }
                yield f"data: {json.dumps(completion_data)}\n\n"
                
            except Exception as e:
                logger.error("Stream chat error: %s", str(e))
                error_data = {
                    'type': 'error',
                    'error': str(e)
                }
                yield f"data: {json.dumps(error_data)}\n\n"
        
        return Response(
            generate(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Authorization, Content-Type',
                'Access-Control-Allow-Methods': 'GET'
            }
        )
        
    except Exception as e:
        logger.error("Chat stream error: %s", str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@llm_bp.route('/chat', methods=['POST'])
def chat():
    """
    AI聊天接口 - 支持可选的JWT认证
    """
    try:
        # 尝试获取用户身份，但不强制要求
        user_id = None
        try:
            from flask_jwt_extended import verify_jwt_in_request
            verify_jwt_in_request(optional=True)
            user_id = get_jwt_identity()
        except Exception:
            # 没有token也可以继续，但功能受限
            pass
            
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({
                'success': False,
                'error': 'Message is required'
            }), 400
            
        message = data['message']
        context = data.get('context', '')
        sensor_id = data.get('sensor_id')
        
        # 获取相关传感器数据作为上下文（仅限已认证用户）
        sensor_context = ""
        if sensor_id and user_id:
            sensor_context = _get_sensor_context(sensor_id)
        
        # 生成AI回复
        response = llm_service.generate_chat_response(
            message=message,
            context=context,
            sensor_context=sensor_context
        )
        
        return jsonify({
            'success': True,
            'response': response['response'],
            'context': response.get('context', ''),
            'timestamp': datetime.now().isoformat(),
            'confidence': response.get('confidence', 0.8),
            'authenticated': user_id is not None
        })
        
    except ValueError as e:
        logger.error("Chat error: %s", str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        logger.error("Chat error: %s", str(e))
        return jsonify({
            'success': False,
            'error': '服务暂时不可用，请稍后再试'
        }), 500

@llm_bp.route('/sensor-analysis', methods=['POST'])
@jwt_required()
def sensor_analysis():
    """
    传感器数据分析和建议
    """
    try:
        data = request.get_json()
        
        if not data or 'sensor_id' not in data:
            return jsonify({
                'success': False,
                'error': 'Sensor ID is required'
            }), 400
            
        sensor_id = data['sensor_id']
        minutes = data.get('minutes', 60)  # 默认分析最近1小时数据
        
        # 获取传感器和最近数据
        sensor = Sensor.query.get(sensor_id)
        if not sensor:
            return jsonify({
                'success': False,
                'error': 'Sensor not found'
            }), 404
            
        # 获取最近数据
        start_time = datetime.now() - timedelta(minutes=minutes)
        readings = Reading.query.filter(
            Reading.sensor_id == sensor_id,
            Reading.timestamp >= start_time
        ).order_by(Reading.timestamp.desc()).limit(100).all()
        
        if not readings:
            return jsonify({
                'success': False,
                'error': 'No recent data found'
            }, 404)
            
        # 分析数据
        analysis = llm_service.analyze_sensor_data(
            sensor=sensor,
            readings=readings
        )
        
        return jsonify({
            'success': True,
            'data': {
                'advice': analysis['advice'],
                'confidence': analysis['confidence'],
                'timestamp': datetime.now().isoformat(),
                'data_points': len(readings),
                'analysis_period': f"{minutes} minutes",
                'recommendations': analysis.get('recommendations', [])
            }
        })
        
    except ValueError as e:
        logger.error("Sensor analysis error: %s", str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        logger.error("Sensor analysis error: %s", str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@llm_bp.route('/agricultural-advice', methods=['POST'])
@jwt_required()
def agricultural_advice():
    """
    获取农业建议
    """
    try:
        data = request.get_json()
        
        # 获取环境参数
        crop_type = data.get('crop_type', '未知作物')
        weather_condition = data.get('weather_condition', '正常')
        soil_moisture = data.get('soil_moisture')
        temperature = data.get('temperature')
        humidity = data.get('humidity')
        
        # 生成农业建议
        advice = llm_service.generate_agricultural_advice(
            crop_type=crop_type,
            weather_condition=weather_condition,
            soil_moisture=soil_moisture,
            temperature=temperature,
            humidity=humidity
        )
        
        return jsonify({
            'success': True,
            'data': {
                'advice': advice['advice'],
                'actions': advice.get('actions', []),
                'urgency': advice.get('urgency', 'low'),
                'timestamp': datetime.now().isoformat()
            }
        })
        
    except ValueError as e:
        logger.error("Agricultural advice error: %s", str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        logger.error("Agricultural advice error: %s", str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@llm_bp.route('/generate-report', methods=['POST'])
@jwt_required()
def generate_report():
    """
    生成智能报告
    """
    try:
        data = request.get_json()
        
        if not data or 'sensor_ids' not in data:
            return jsonify({
                'success': False,
                'error': 'Sensor IDs are required'
            }), 400
            
        sensor_ids = data['sensor_ids']
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        report_type = data.get('report_type', 'daily')
        
        # 解析日期
        if start_date:
            start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        else:
            start_date = datetime.now() - timedelta(days=1)
            
        if end_date:
            end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        else:
            end_date = datetime.now()
            
        # 获取传感器数据
        sensors_data = []
        for sensor_id in sensor_ids:
            sensor = Sensor.query.get(sensor_id)
            if not sensor:
                continue
                
            readings = Reading.query.filter(
                Reading.sensor_id == sensor_id,
                Reading.timestamp >= start_date,
                Reading.timestamp <= end_date
            ).order_by(Reading.timestamp.desc()).all()
            
            sensors_data.append({
                'sensor': sensor,
                'readings': readings
            })
            
        # 生成报告
        report = llm_service.generate_report(
            sensors_data=sensors_data,
            report_type=report_type,
            start_date=start_date,
            end_date=end_date
        )
        
        return jsonify({
            'success': True,
            'data': {
                'report': report['report'],
                'summary': report.get('summary', ''),
                'recommendations': report.get('recommendations', []),
                'timestamp': datetime.now().isoformat()
            }
        })
        
    except ValueError as e:
        logger.error("Report generation error: %s", str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        logger.error("Report generation error: %s", str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@llm_bp.route('/system-diagnosis', methods=['POST'])
@jwt_required()
def system_diagnosis():
    """
    系统诊断和建议
    """
    try:
        user_id = get_jwt_identity()
        
        # 获取系统状态数据
        devices_count = Device.query.filter_by(status='active').count()
        sensors_count = Sensor.query.filter_by(status='active').count()
        active_alarms = Alarm.query.filter_by(status='active').count()
        
        # 获取最近24小时的数据点数
        yesterday = datetime.now() - timedelta(days=1)
        recent_readings = Reading.query.filter(
            Reading.timestamp >= yesterday
        ).count()
        
        # 获取异常传感器
        problem_sensors = []
        sensors = Sensor.query.filter_by(status='active').all()
        for sensor in sensors:
            latest_reading = Reading.query.filter_by(sensor_id=sensor.id)\
                .order_by(Reading.timestamp.desc()).first()
            if not latest_reading or \
               (datetime.now() - latest_reading.timestamp).total_seconds() > 3600:
                problem_sensors.append(sensor)
        
        # 生成系统诊断
        diagnosis = llm_service.generate_system_diagnosis(
            devices_count=devices_count,
            sensors_count=sensors_count,
            active_alarms=active_alarms,
            recent_readings=recent_readings,
            problem_sensors=problem_sensors
        )
        
        return jsonify({
            'success': True,
            'data': {
                'diagnosis': diagnosis['diagnosis'],
                'health_score': diagnosis.get('health_score', 85),
                'recommendations': diagnosis.get('recommendations', []),
                'priority_actions': diagnosis.get('priority_actions', []),
                'timestamp': datetime.now().isoformat()
            }
        })
        
    except ValueError as e:
        logger.error("System diagnosis error: %s", str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        logger.error("System diagnosis error: %s", str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@llm_bp.route('/quick-actions', methods=['GET'])
@jwt_required()
def get_quick_actions():
    """
    获取快捷操作建议
    """
    try:
        # 获取当前系统状态
        active_alarms = Alarm.query.filter_by(status='active').limit(5).all()
        
        # 生成快捷操作
        quick_actions = llm_service.generate_quick_actions(
            active_alarms=active_alarms
        )
        
        return jsonify({
            'success': True,
            'data': {
                'actions': quick_actions,
                'timestamp': datetime.now().isoformat()
            }
        })
        
    except ValueError as e:
        logger.error("Quick actions error: %s", str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        logger.error("Quick actions error: %s", str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def _get_sensor_context(sensor_id: int) -> str:
    """获取传感器上下文信息"""
    try:
        sensor = Sensor.query.get(sensor_id)
        if not sensor:
            return ""
            
        # 获取设备信息
        device = Device.query.get(sensor.device_id)
        
        # 获取最近几个读数
        recent_readings = Reading.query.filter_by(sensor_id=sensor_id)\
            .order_by(Reading.timestamp.desc()).limit(5).all()
        
        # 获取活跃告警
        active_alarms = Alarm.query.filter_by(
            sensor_id=sensor_id,
            status='active'
        ).all()
        
        context = f"传感器 {sensor.name} (类型: {sensor.sensor_type}, 单位: {sensor.unit})"
        if device:
            context += f", 所属设备: {device.name} (位置: {device.location})"
        
        if recent_readings:
            context += f", 最近读数: {[r.numeric_value for r in recent_readings]}"
        
        if active_alarms:
            context += f", 活跃告警: {len(active_alarms)}个"
        
        return context
        
    except ValueError as e:
        logger.error("Get sensor context error: %s", str(e))
        return ""
    except Exception as e:
        logger.error("Get sensor context error: %s", str(e))
        return ""

def _get_recent_sensor_context() -> str:
    """获取最近的传感器上下文信息"""
    try:
        # 获取最近活跃的传感器（有数据的）
        recent_time = datetime.now() - timedelta(minutes=30)
        recent_sensors = db.session.query(Sensor).join(Reading).filter(
            Reading.timestamp >= recent_time
        ).distinct().limit(5).all()
        
        if not recent_sensors:
            return "暂无最近传感器数据"
        
        context_parts = []
        for sensor in recent_sensors:
            # 获取该传感器最新读数
            latest_reading = Reading.query.filter_by(sensor_id=sensor.id)\
                .order_by(Reading.timestamp.desc()).first()
            
            if latest_reading:
                device = Device.query.get(sensor.device_id)
                device_info = f" ({device.location})" if device else ""
                
                context_parts.append(
                    f"{sensor.name}{device_info}: {latest_reading.numeric_value}{sensor.unit}"
                )
        
        return "最近传感器数据: " + ", ".join(context_parts)
        
    except Exception as e:
        logger.error("Get recent sensor context error: %s", str(e))
        return "传感器数据获取失败"
