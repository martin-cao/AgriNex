"""
设备模板管理控制器
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from models.device_template import DeviceTemplate
from extensions import db
import logging

# 创建蓝图
device_template_bp = Blueprint('device_template', __name__)

logger = logging.getLogger(__name__)

@device_template_bp.route('', methods=['GET'])
@device_template_bp.route('/', methods=['GET'])
@jwt_required()
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

@device_template_bp.route('/<device_type>', methods=['GET'])
@jwt_required()
def get_device_template(device_type: str):
    """获取特定设备模板"""
    try:
        template = DeviceTemplate.get_by_device_type(device_type)
        if not template:
            return jsonify({
                'success': False,
                'error': f'Device template for type "{device_type}" not found'
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

@device_template_bp.route('', methods=['POST'])
@device_template_bp.route('/', methods=['POST'])
@jwt_required()
def create_device_template():
    """创建新设备模板"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # 验证必需字段
        required_fields = ['device_type', 'name', 'sensor_configs']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # 检查设备类型是否已存在
        existing_template = DeviceTemplate.get_by_device_type(data['device_type'])
        if existing_template:
            return jsonify({
                'success': False,
                'error': f'Device template for type "{data["device_type"]}" already exists'
            }), 400
        
        # 验证传感器配置格式
        sensor_configs = data['sensor_configs']
        if not isinstance(sensor_configs, list):
            return jsonify({
                'success': False,
                'error': 'sensor_configs must be a list'
            }), 400
        
        for i, config in enumerate(sensor_configs):
            required_sensor_fields = ['type', 'name', 'unit']
            for field in required_sensor_fields:
                if field not in config:
                    return jsonify({
                        'success': False,
                        'error': f'Missing required field "{field}" in sensor config {i}'
                    }), 400
        
        # 创建设备模板
        template = DeviceTemplate.create_with_sensors(
            device_type=data['device_type'],
            name=data['name'],
            description=data.get('description', ''),
            sensor_configs=data['sensor_configs'],
            manufacturer=data.get('manufacturer'),
            model=data.get('model'),
            default_config=data.get('default_config', {}),
            is_active=data.get('is_active', True)
        )
        
        db.session.commit()
        logger.info("Created device template: %s", template.name)
        
        return jsonify({
            'success': True,
            'data': template.to_dict(),
            'message': f'Device template "{template.name}" created successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error("Error creating device template: %s", str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@device_template_bp.route('/<device_type>', methods=['PUT'])
@jwt_required()
def update_device_template(device_type: str):
    """更新设备模板"""
    try:
        template = DeviceTemplate.get_by_device_type(device_type)
        if not template:
            return jsonify({
                'success': False,
                'error': f'Device template for type "{device_type}" not found'
            }), 404
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # 更新允许的字段
        allowed_fields = ['name', 'description', 'manufacturer', 'model', 
                         'sensor_configs', 'default_config', 'is_active']
        
        for field in allowed_fields:
            if field in data:
                setattr(template, field, data[field])
        
        # 更新时间戳
        from datetime import datetime
        template.updated_at = datetime.utcnow()
        
        db.session.commit()
        logger.info("Updated device template: %s", template.name)
        
        return jsonify({
            'success': True,
            'data': template.to_dict(),
            'message': f'Device template "{template.name}" updated successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error("Error updating device template %s: %s", device_type, str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@device_template_bp.route('/<device_type>', methods=['DELETE'])
@jwt_required()
def delete_device_template(device_type: str):
    """删除设备模板（软删除）"""
    try:
        template = DeviceTemplate.get_by_device_type(device_type)
        if not template:
            return jsonify({
                'success': False,
                'error': f'Device template for type "{device_type}" not found'
            }), 404
        
        # 检查是否有设备使用此模板
        from models.device import Device
        devices_using_template = Device.query.filter_by(type=device_type).count()
        
        if devices_using_template > 0:
            return jsonify({
                'success': False,
                'error': f'Cannot delete template: {devices_using_template} devices are using this template'
            }), 400
        
        # 软删除：设置为非活跃状态
        template.is_active = False
        from datetime import datetime
        template.updated_at = datetime.utcnow()
        
        db.session.commit()
        logger.info("Deactivated device template: %s", template.name)
        
        return jsonify({
            'success': True,
            'message': f'Device template "{template.name}" deactivated successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error("Error deleting device template %s: %s", device_type, str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@device_template_bp.route('/<device_type>/sensors', methods=['GET'])
@jwt_required()
def get_template_sensors(device_type: str):
    """获取设备模板的传感器配置"""
    try:
        template = DeviceTemplate.get_by_device_type(device_type)
        if not template:
            return jsonify({
                'success': False,
                'error': f'Device template for type "{device_type}" not found'
            }), 404
        
        sensor_configs = template.get_sensor_configs()
        
        return jsonify({
            'success': True,
            'data': sensor_configs,
            'total': len(sensor_configs),
            'required_sensors': len(template.get_required_sensors())
        })
        
    except Exception as e:
        logger.error("Error getting template sensors %s: %s", device_type, str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@device_template_bp.route('/<device_type>/validate', methods=['POST'])
@jwt_required()
def validate_sensor_for_template(device_type: str):
    """验证传感器类型是否适用于设备模板"""
    try:
        template = DeviceTemplate.get_by_device_type(device_type)
        if not template:
            return jsonify({
                'success': False,
                'error': f'Device template for type "{device_type}" not found'
            }), 404
        
        data = request.get_json()
        if not data or 'sensor_type' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing sensor_type field'
            }), 400
        
        sensor_type = data['sensor_type']
        is_valid = template.validate_sensor_type(sensor_type)
        
        if is_valid:
            # 获取传感器配置
            sensor_configs = template.get_sensor_configs()
            sensor_config = next((config for config in sensor_configs 
                                 if config['type'] == sensor_type), None)
            
            return jsonify({
                'success': True,
                'valid': True,
                'sensor_config': sensor_config,
                'message': f'Sensor type "{sensor_type}" is valid for device type "{device_type}"'
            })
        else:
            allowed_types = [config['type'] for config in template.get_sensor_configs()]
            return jsonify({
                'success': True,
                'valid': False,
                'allowed_types': allowed_types,
                'message': f'Sensor type "{sensor_type}" is not valid for device type "{device_type}"'
            })
        
    except Exception as e:
        logger.error("Error validating sensor for template %s: %s", device_type, str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
