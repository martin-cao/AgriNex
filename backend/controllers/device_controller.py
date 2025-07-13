# backend/controllers/device_controller.py
"""
设备管理控制器 - MySQL Only版本
移除所有Mock数据，只支持真实的数据库操作
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
import logging
import asyncio
from services.device_validation_service import device_validation_service

# 导入数据库模型
from models.device import Device
from models.sensor import Sensor
from models.reading import Reading
from extensions import db

# 导入设备模板
from models.device_template import DeviceTemplate

# 创建蓝图
device_bp = Blueprint('device', __name__)

logger = logging.getLogger(__name__)

# 设备相关API
@device_bp.route('', methods=['GET'])
@device_bp.route('/', methods=['GET'])
def get_devices():
    """获取所有设备"""
    try:
        devices = Device.query.all()
        device_list = [device.to_dict() for device in devices]  # 使用模型的to_dict方法
        
        return jsonify({
            'success': True,
            'data': device_list,
            'total': len(device_list)
        })
    except Exception as e:
        logger.error("Error getting devices: %s", str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@device_bp.route('/<int:device_id>', methods=['GET'])
def get_device(device_id: int):
    """获取特定设备"""
    try:
        device = Device.query.get(device_id)
        if not device:
            return jsonify({
                'success': False,
                'error': 'Device not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': device.to_dict()  # 使用模型的to_dict方法
        })
    except Exception as e:
        logger.error("Error getting device %d: %s", device_id, str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@device_bp.route('', methods=['POST'])
@device_bp.route('/', methods=['POST'])
def create_device():
    """创建新设备"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # 验证必需字段
        required_fields = ['name', 'device_type']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # 检查client_id是否已存在（如果提供了）
        if 'client_id' in data and data['client_id']:
            existing_device = Device.query.filter_by(client_id=data['client_id']).first()
            if existing_device:
                return jsonify({
                    'success': False,
                    'error': f'Device with client_id "{data["client_id"]}" already exists'
                }), 400
        
        # 验证设备类型是否有对应的模板
        device_template = DeviceTemplate.get_by_device_type(data['device_type'])
        if not device_template:
            return jsonify({
                'success': False,
                'error': f'Unsupported device type: {data["device_type"]}. Please create a device template first.'
            }), 400
        
        # 创建设备
        device = Device.create(
            name=data['name'],
            location=data.get('location'),
            device_type=data['device_type'],
            status=data.get('status', 'active'),
            ip_address=data.get('ip_address'),
            port=data.get('port'),
            is_active=data.get('is_active', True),
            client_id=data.get('client_id')
        )
        
        # 立即flush设备以获取ID
        db.session.flush()
        
        # 根据设备模板自动创建必需的传感器
        sensor_configs = device_template.get_sensor_configs()
        created_sensors = []
        
        for sensor_config in sensor_configs:
            # 只创建必需的传感器，或用户明确指定的传感器
            if sensor_config.get('is_required', True):
                sensor = Sensor.create(
                    device_id=device.id,
                    sensor_type=sensor_config['type'],
                    name=sensor_config['name'],
                    unit=sensor_config['unit'],
                    status='active'
                )
                created_sensors.append(sensor)
        
        db.session.commit()
        logger.info("Created device: %s with %d sensors", device.name, len(created_sensors))
        
        # 返回设备信息和创建的传感器列表
        result = device.to_dict()
        result['sensors'] = [sensor.to_dict() for sensor in created_sensors]
        result['device_template'] = device_template.to_dict()
        
        return jsonify({
            'success': True,
            'data': result,
            'message': f'Device created successfully with {len(created_sensors)} sensors'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error("Error creating device: %s", str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@device_bp.route('/<int:device_id>', methods=['PUT'])
def update_device(device_id: int):
    """更新设备"""
    try:
        device = Device.query.get(device_id)
        if not device:
            return jsonify({
                'success': False,
                'error': 'Device not found'
            }), 404
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # 如果更新client_id，检查是否冲突
        if 'client_id' in data and data['client_id'] != device.client_id:
            existing_device = Device.query.filter_by(client_id=data['client_id']).first()
            if existing_device and existing_device.id != device_id:
                return jsonify({
                    'success': False,
                    'error': f'Device with client_id "{data["client_id"]}" already exists'
                }), 400
        
        # 更新设备
        device.update(**data)
        db.session.commit()
        logger.info("Updated device: %s", device.name)
        
        return jsonify({
            'success': True,
            'data': device.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error("Error updating device %d: %s", device_id, str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@device_bp.route('/<int:device_id>', methods=['DELETE'])
def delete_device(device_id: int):
    """删除设备"""
    try:
        device = Device.query.get(device_id)
        if not device:
            return jsonify({
                'success': False,
                'error': 'Device not found'
            }), 404
        
        # 软删除：标记为删除状态
        device.delete()
        db.session.commit()
        logger.info("Deleted device: %s", device.name)
        
        return jsonify({
            'success': True,
            'data': {}
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error("Error deleting device %d: %s", device_id, str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# 传感器相关API
@device_bp.route('/<int:device_id>/sensors', methods=['GET'])
def get_device_sensors(device_id: int):
    """获取设备的所有传感器"""
    try:
        # 先检查设备是否存在
        device = Device.query.get(device_id)
        if not device:
            return jsonify({
                'success': False,
                'error': 'Device not found'
            }), 404
        
        sensors = Sensor.query.filter_by(device_id=device_id).all()
        sensor_list = [sensor.to_dict() for sensor in sensors]  # 使用模型的to_dict方法
        
        return jsonify({
            'success': True,
            'data': sensor_list,
            'total': len(sensor_list)
        })
    except Exception as e:
        logger.error("Error getting sensors for device %d: %s", device_id, str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@device_bp.route('/<int:device_id>/sensors/<int:sensor_id>/latest', methods=['GET'])
def get_latest_reading(device_id: int, sensor_id: int):
    """获取传感器最新读数"""
    try:
        # 验证传感器属于指定设备
        sensor = Sensor.query.filter_by(id=sensor_id, device_id=device_id).first()
        if not sensor:
            return jsonify({
                'success': False,
                'error': 'Sensor not found'
            }), 404
        
        # 获取最新读数
        reading = Reading.query.filter_by(sensor_id=sensor_id).order_by(Reading.timestamp.desc()).first()
        if not reading:
            return jsonify({
                'success': False,
                'error': 'No readings found'
            }), 404
        
        reading_data = {
            'id': reading.id,
            'sensor_id': reading.sensor_id,
            'timestamp': reading.timestamp.isoformat(),
            'numeric_value': reading.numeric_value,
            'text_value': reading.text_value,
            'file_path': reading.file_path
        }
        
        return jsonify({
            'success': True,
            'data': reading_data
        })
    except Exception as e:
        logger.error("Error getting latest reading for sensor %d: %s", sensor_id, str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@device_bp.route('/<int:device_id>/sensors/<int:sensor_id>/readings', methods=['GET'])
def get_sensor_readings(device_id: int, sensor_id: int):
    """获取传感器读数列表"""
    try:
        # 验证传感器属于指定设备
        sensor = Sensor.query.filter_by(id=sensor_id, device_id=device_id).first()
        if not sensor:
            return jsonify({
                'success': False,
                'error': 'Sensor not found'
            }), 404
        
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 100, type=int)
        
        # 查询读数
        query = Reading.query.filter_by(sensor_id=sensor_id).order_by(Reading.timestamp.desc())
        total = query.count()
        readings = query.offset((page - 1) * limit).limit(limit).all()
        
        reading_list = []
        for reading in readings:
            reading_list.append({
                'id': reading.id,
                'sensor_id': reading.sensor_id,
                'timestamp': reading.timestamp.isoformat(),
                'numeric_value': reading.numeric_value,
                'text_value': reading.text_value,
                'file_path': reading.file_path
            })
        
        return jsonify({
            'success': True,
            'data': reading_list,
            'total': total,
            'page': page,
            'limit': limit,
            'has_next': (page * limit) < total
        })
    except Exception as e:
        logger.error("Error getting readings for sensor %d: %s", sensor_id, str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@device_bp.route('/<int:device_id>/sensors', methods=['POST'])
def add_sensor_to_device(device_id: int):
    """为设备添加传感器 - 只能添加设备模板定义的传感器类型"""
    try:
        # 验证设备存在
        device = Device.query.get(device_id)
        if not device:
            return jsonify({
                'success': False,
                'error': 'Device not found'
            }), 404
        
        # 获取设备模板
        device_template = DeviceTemplate.get_by_device_type(device.type)
        if not device_template:
            return jsonify({
                'success': False,
                'error': f'No template found for device type: {device.type}'
            }), 400
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # 验证必需字段
        required_fields = ['sensor_type']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # 验证传感器类型是否在设备模板中定义
        if not device_template.validate_sensor_type(data['sensor_type']):
            allowed_types = [config['type'] for config in device_template.get_sensor_configs()]
            return jsonify({
                'success': False,
                'error': f'Sensor type "{data["sensor_type"]}" is not allowed for device type "{device.type}". Allowed types: {allowed_types}'
            }), 400
        
        # 检查是否已存在相同类型的传感器
        existing_sensor = Sensor.query.filter_by(
            device_id=device_id,
            type=data['sensor_type']
        ).first()
        
        if existing_sensor:
            return jsonify({
                'success': False,
                'error': f'Sensor of type "{data["sensor_type"]}" already exists for this device'
            }), 400
        
        # 从设备模板获取传感器配置
        sensor_configs = device_template.get_sensor_configs()
        sensor_template = next((config for config in sensor_configs 
                               if config['type'] == data['sensor_type']), None)
        
        if not sensor_template:
            return jsonify({
                'success': False,
                'error': f'Sensor template not found for type: {data["sensor_type"]}'
            }), 400
        
        # 创建传感器（使用模板默认值或用户提供的值）
        sensor = Sensor.create(
            device_id=device_id,
            sensor_type=data['sensor_type'],
            name=data.get('name', sensor_template['name']),
            unit=data.get('unit', sensor_template['unit']),
            status=data.get('status', 'active')
        )
        
        db.session.commit()
        logger.info("Added sensor %s to device %s", sensor.name, device.name)
        
        return jsonify({
            'success': True,
            'data': sensor.to_dict(),
            'message': 'Sensor added successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error("Error adding sensor to device %d: %s", device_id, str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@device_bp.route('/templates', methods=['GET'])
def get_device_templates():
    """获取所有设备模板"""
    try:
        templates = DeviceTemplate.get_all_active()
        template_list = [template.to_dict() for template in templates]
        
        return jsonify({
            'success': True,
            'data': template_list,
            'total': len(template_list)
        })
    except Exception as e:
        logger.error("Error getting device templates: %s", str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@device_bp.route('/templates/<device_type>', methods=['GET'])
def get_device_template(device_type: str):
    """获取特定设备类型的模板"""
    try:
        template = DeviceTemplate.get_by_device_type(device_type)
        if not template:
            return jsonify({
                'success': False,
                'error': f'Template not found for device type: {device_type}'
            }), 404
        
        return jsonify({
            'success': True,
            'data': template.to_dict()
        })
    except Exception as e:
        logger.error("Error getting device template %s: %s", device_type, str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# 健康检查
@device_bp.route('/health', methods=['GET'])
def health_check():
    """设备服务健康检查"""
    try:
        # 测试数据库连接
        Device.query.count()
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'message': 'Device service is running without mock data',
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error("Health check failed: %s", str(e))
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500


@device_bp.route('/validate', methods=['POST'])
def validate_device():
    """验证手动添加的设备"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        
        # 验证必需字段
        required_fields = ['device_id', 'address', 'device_type', 'name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'缺少必需字段: {field}'
                }), 400
        
        # 检查设备ID是否已存在
        existing_device = Device.query.filter_by(name=data['device_id']).first()
        if existing_device:
            return jsonify({
                'success': False,
                'message': f'设备ID {data["device_id"]} 已存在'
            }), 400
        
        # 运行异步验证
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            success, message, mqtt_data = loop.run_until_complete(
                device_validation_service.validate_device(data)
            )
        finally:
            loop.close()
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'mqtt_data': mqtt_data,
                'device_data': data
            })
        else:
            return jsonify({
                'success': False,
                'message': message,
                'mqtt_data': mqtt_data
            }), 400
            
    except Exception as e:
        logger.error("设备验证失败: %s", str(e))
        return jsonify({
            'success': False,
            'message': f'验证过程出错: {str(e)}'
        }), 500


@device_bp.route('/register', methods=['POST'])
def register_validated_device():
    """注册已验证的设备"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        
        # 验证必需字段
        required_fields = ['device_id', 'address', 'device_type', 'name', 'location']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'缺少必需字段: {field}'
                }), 400
        
        # 再次检查设备ID是否已存在
        existing_device = Device.query.filter_by(name=data['device_id']).first()
        if existing_device:
            return jsonify({
                'success': False,
                'message': f'设备ID {data["device_id"]} 已存在'
            }), 400
        
        # 创建设备记录
        device = Device.create(
            name=data['device_id'],  # 使用device_id作为name
            location=data['location'],
            device_type=data['device_type'],
            status='active'
        )
        
        # 创建默认传感器（基于设备类型）
        sensor_configs = _get_sensor_configs_by_device_type(data['device_type'])
        
        for sensor_config in sensor_configs:
            from models.sensor import Sensor
            sensor = Sensor.create(
                device_id=device.id,
                sensor_type=sensor_config['type'],
                name=sensor_config['description'],
                unit=sensor_config.get('unit', ''),
                status='active'
            )
        
        # 提交数据库事务
        db.session.commit()
        
        logger.info(f"设备注册成功: {data['device_id']}")
        
        return jsonify({
            'success': True,
            'message': '设备注册成功',
            'device': device.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error("设备注册失败: %s", str(e))
        return jsonify({
            'success': False,
            'message': f'注册失败: {str(e)}'
        }), 500


@device_bp.route('/<device_id>/mqtt-status', methods=['GET'])
def get_device_mqtt_status(device_id: str):
    """检查设备MQTT连接状态"""
    try:
        # 查找设备
        device = Device.query.filter_by(name=device_id).first()
        if not device:
            return jsonify({
                'success': False,
                'message': '设备不存在'
            }), 404
        
        # 获取设备最新的数据读取时间
        from models.sensor import Sensor
        from models.reading import Reading
        
        latest_reading = db.session.query(Reading).join(Sensor).filter(
            Sensor.device_id == device.id
        ).order_by(Reading.timestamp.desc()).first()
        
        if latest_reading:
            time_diff = datetime.utcnow() - latest_reading.timestamp
            is_online = time_diff.total_seconds() < 300  # 5分钟内有数据认为在线
            
            return jsonify({
                'success': True,
                'data': {
                    'device_id': device_id,
                    'is_online': is_online,
                    'last_seen': latest_reading.timestamp.isoformat(),
                    'seconds_since_last_data': int(time_diff.total_seconds())
                }
            })
        else:
            return jsonify({
                'success': True,
                'data': {
                    'device_id': device_id,
                    'is_online': False,
                    'last_seen': None,
                    'seconds_since_last_data': None
                }
            })
            
    except Exception as e:
        logger.error("获取设备MQTT状态失败: %s", str(e))
        return jsonify({
            'success': False,
            'message': f'获取状态失败: {str(e)}'
        }), 500


@device_bp.route('/sensor-types', methods=['GET'])
def get_sensor_types():
    """获取所有可用的传感器类型"""
    try:
        from models.device_template import DeviceTemplate
        
        # 获取传感器类型参数
        category = request.args.get('category')
        
        if category:
            sensor_types = DeviceTemplate.get_sensor_types_by_category(category)
        else:
            sensor_types = DeviceTemplate.get_available_sensor_types()
        
        # 添加分类信息
        categories = {}
        for sensor_type, info in sensor_types.items():
            cat = info.get('category', 'unknown')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append({
                'type': sensor_type,
                'name': info['name'],
                'unit': info['unit']
            })
        
        return jsonify({
            'success': True,
            'data': {
                'sensor_types': sensor_types,
                'categories': categories,
                'total': len(sensor_types)
            }
        })
        
    except Exception as e:
        logger.error("Error getting sensor types: %s", str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@device_bp.route('/device-categories', methods=['GET'])
def get_device_categories():
    """获取设备分类统计"""
    try:
        from models.device_template import DEVICE_CATEGORIES
        
        # 获取每个分类的设备模板数量
        templates = DeviceTemplate.get_all_active()
        category_stats = {}
        
        for template in templates:
            # 根据设备类型推断分类
            device_type = template.device_type
            category = 'basic'  # 默认分类
            
            if 'greenhouse' in device_type or 'control' in device_type:
                category = 'greenhouse'
            elif 'soil' in device_type or 'farm' in device_type:
                category = 'field'
            elif 'livestock' in device_type:
                category = 'livestock'
            elif 'aquaculture' in device_type:
                category = 'aquaculture'
            elif 'storage' in device_type:
                category = 'storage'
            elif 'drone' in device_type:
                category = 'mobile'
            elif 'irrigation' in device_type or 'water' in device_type:
                category = 'control'
            
            if category not in category_stats:
                category_stats[category] = {
                    'name': DEVICE_CATEGORIES.get(category, category),
                    'count': 0,
                    'devices': []
                }
            
            category_stats[category]['count'] += 1
            category_stats[category]['devices'].append({
                'device_type': template.device_type,
                'name': template.name,
                'description': template.description
            })
        
        return jsonify({
            'success': True,
            'data': {
                'categories': category_stats,
                'total_categories': len(category_stats),
                'total_templates': len(templates)
            }
        })
        
    except Exception as e:
        logger.error("Error getting device categories: %s", str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def _get_sensor_configs_by_device_type(device_type: str):
    """根据设备类型获取传感器配置"""
    configs = {
        'soil_sensor': [
            {'type': 'soil_moisture', 'description': '土壤湿度', 'unit': '%'},
            {'type': 'soil_temperature', 'description': '土壤温度', 'unit': '°C'},
            {'type': 'soil_ph', 'description': '土壤pH值', 'unit': 'pH'}
        ],
        'weather_station': [
            {'type': 'air_temperature', 'description': '空气温度', 'unit': '°C'},
            {'type': 'air_humidity', 'description': '空气湿度', 'unit': '%'},
            {'type': 'atmospheric_pressure', 'description': '大气压强', 'unit': 'hPa'},
            {'type': 'wind_speed', 'description': '风速', 'unit': 'm/s'}
        ],
        'irrigation_controller': [
            {'type': 'water_flow', 'description': '水流量', 'unit': 'L/min'},
            {'type': 'water_pressure', 'description': '水压', 'unit': 'bar'},
            {'type': 'valve_status', 'description': '阀门状态', 'unit': ''}
        ]
    }
    
    return configs.get(device_type, [
        {'type': 'generic_sensor', 'description': '通用传感器', 'unit': ''}
    ])
