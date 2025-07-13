"""
设备模板模型 - 定义设备类型和预配置传感器
"""
from extensions import db
from datetime import datetime
from typing import List, Dict, Any, Optional


class DeviceTemplate(db.Model):
    """设备模板 - 定义不同类型设备的标准配置"""
    __tablename__ = 'device_templates'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    device_type = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    manufacturer = db.Column(db.String(255))
    model = db.Column(db.String(255))
    
    # 传感器配置JSON字段
    sensor_configs = db.Column(db.JSON, nullable=False)
    
    # 设备默认配置
    default_config = db.Column(db.JSON, default=dict)
    
    # 状态和时间戳
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'device_type': self.device_type,
            'name': self.name,
            'description': self.description,
            'manufacturer': self.manufacturer,
            'model': self.model,
            'sensor_configs': self.sensor_configs,
            'default_config': self.default_config,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_sensor_configs(self) -> List[Dict[str, Any]]:
        """获取传感器配置列表"""
        return self.sensor_configs or []
    
    def add_sensor_config(self, sensor_type: str, name: str, unit: str, 
                         description: Optional[str] = None, **kwargs):
        """添加传感器配置"""
        if not self.sensor_configs:
            self.sensor_configs = []
        
        sensor_config = {
            'type': sensor_type,
            'name': name,
            'unit': unit,
            'description': description or name,
            'is_required': kwargs.get('is_required', True),
            'default_config': kwargs.get('default_config', {}),
            'validation_rules': kwargs.get('validation_rules', {})
        }
        
        self.sensor_configs.append(sensor_config)
        self.updated_at = datetime.utcnow()
    
    @classmethod
    def create_with_sensors(cls, device_type: str, name: str, description: str,
                           sensor_configs: List[Dict[str, Any]], **kwargs):
        """创建包含传感器配置的设备模板"""
        template = cls()
        template.device_type = device_type
        template.name = name
        template.description = description
        template.manufacturer = kwargs.get('manufacturer')
        template.model = kwargs.get('model')
        template.sensor_configs = sensor_configs
        template.default_config = kwargs.get('default_config', {})
        template.is_active = kwargs.get('is_active', True)
        
        db.session.add(template)
        return template
    
    @classmethod
    def get_by_device_type(cls, device_type: str):
        """根据设备类型获取模板"""
        return cls.query.filter_by(device_type=device_type, is_active=True).first()
    
    @classmethod
    def get_all_active(cls):
        """获取所有活跃的设备模板"""
        return cls.query.filter_by(is_active=True).all()
    
    def validate_sensor_type(self, sensor_type: str) -> bool:
        """验证传感器类型是否属于该设备模板"""
        sensor_types = [config['type'] for config in self.get_sensor_configs()]
        return sensor_type in sensor_types
    
    def get_required_sensors(self) -> List[Dict[str, Any]]:
        """获取必需的传感器配置"""
        return [config for config in self.get_sensor_configs() 
                if config.get('is_required', True)]
    
    @classmethod
    def get_sensor_type_info(cls, sensor_type: str) -> Dict[str, Any]:
        """获取传感器类型信息"""
        return SENSOR_TYPES.get(sensor_type, {
            'name': f'未知传感器({sensor_type})',
            'unit': 'unknown',
            'category': 'unknown'
        })
    
    @classmethod
    def get_available_sensor_types(cls) -> Dict[str, Dict[str, Any]]:
        """获取所有可用的传感器类型"""
        return SENSOR_TYPES
    
    @classmethod
    def get_sensor_types_by_category(cls, category: str) -> Dict[str, Dict[str, Any]]:
        """根据分类获取传感器类型"""
        return {k: v for k, v in SENSOR_TYPES.items() if v.get('category') == category}
    
    @classmethod
    def validate_device_config(cls, device_type: str, sensor_configs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """验证设备配置"""
        errors = []
        warnings = []
        
        # 验证传感器类型
        for config in sensor_configs:
            sensor_type = config.get('type')
            if sensor_type not in SENSOR_TYPES:
                errors.append(f"未知的传感器类型: {sensor_type}")
            
            # 验证必需字段
            required_fields = ['type', 'name', 'unit']
            for field in required_fields:
                if not config.get(field):
                    errors.append(f"传感器配置缺少必需字段: {field}")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def __repr__(self):
        return f"<DeviceTemplate(type='{self.device_type}', name='{self.name}')>"


# 预定义设备模板数据
PREDEFINED_DEVICE_TEMPLATES = [
    {
        'device_type': 'smart_farm',
        'name': '智慧农场设备',
        'description': '综合性农业监测设备，包含土壤、环境等多种传感器',
        'manufacturer': 'AgriNex',
        'model': 'SF-2024',
        'sensor_configs': [
            {
                'type': 'temperature',
                'name': '环境温度传感器',
                'unit': '°C',
                'description': '监测环境温度',
                'is_required': True,
                'validation_rules': {'min': -40, 'max': 80}
            },
            {
                'type': 'humidity',
                'name': '环境湿度传感器',
                'unit': '%',
                'description': '监测空气湿度',
                'is_required': True,
                'validation_rules': {'min': 0, 'max': 100}
            },
            {
                'type': 'light',
                'name': '光照强度传感器',
                'unit': 'lux',
                'description': '监测光照强度',
                'is_required': True,
                'validation_rules': {'min': 0, 'max': 10000}
            },
            {
                'type': 'soil_moisture',
                'name': '土壤湿度传感器',
                'unit': '%',
                'description': '监测土壤含水量',
                'is_required': True,
                'validation_rules': {'min': 0, 'max': 100}
            },
            {
                'type': 'soil_ph',
                'name': '土壤pH传感器',
                'unit': 'pH',
                'description': '监测土壤酸碱度',
                'is_required': False,
                'validation_rules': {'min': 0, 'max': 14}
            },
            {
                'type': 'soil_ec',
                'name': '土壤EC传感器',
                'unit': 'mS/cm',
                'description': '监测土壤电导率',
                'is_required': False,
                'validation_rules': {'min': 0, 'max': 10}
            }
        ],
        'default_config': {
            'collection_interval': 30,
            'data_retention_days': 365,
            'alert_enabled': True
        }
    },
    {
        'device_type': 'weather_station',
        'name': '气象站设备',
        'description': '专业气象监测设备，提供全面的天气数据',
        'manufacturer': 'AgriNex',
        'model': 'WS-2024',
        'sensor_configs': [
            {
                'type': 'temperature',
                'name': '气温传感器',
                'unit': '°C',
                'description': '监测大气温度',
                'is_required': True,
                'validation_rules': {'min': -50, 'max': 60}
            },
            {
                'type': 'humidity',
                'name': '湿度传感器',
                'unit': '%',
                'description': '监测空气湿度',
                'is_required': True,
                'validation_rules': {'min': 0, 'max': 100}
            },
            {
                'type': 'pressure',
                'name': '气压传感器',
                'unit': 'hPa',
                'description': '监测大气压强',
                'is_required': True,
                'validation_rules': {'min': 800, 'max': 1200}
            },
            {
                'type': 'wind_speed',
                'name': '风速传感器',
                'unit': 'm/s',
                'description': '监测风速',
                'is_required': True,
                'validation_rules': {'min': 0, 'max': 50}
            },
            {
                'type': 'wind_direction',
                'name': '风向传感器',
                'unit': '°',
                'description': '监测风向',
                'is_required': False,
                'validation_rules': {'min': 0, 'max': 360}
            },
            {
                'type': 'rain_level',
                'name': '雨量传感器',
                'unit': 'mm',
                'description': '监测降雨量',
                'is_required': False,
                'validation_rules': {'min': 0, 'max': 200}
            },
            {
                'type': 'uv_index',
                'name': 'UV指数传感器',
                'unit': 'UV',
                'description': '监测紫外线指数',
                'is_required': False,
                'validation_rules': {'min': 0, 'max': 15}
            }
        ],
        'default_config': {
            'collection_interval': 60,
            'data_retention_days': 1095,  # 3年
            'alert_enabled': True
        }
    },
    {
        'device_type': 'environmental_monitor',
        'name': '环境监测设备',
        'description': '室内外环境质量监测设备',
        'manufacturer': 'AgriNex',
        'model': 'EM-2024',
        'sensor_configs': [
            {
                'type': 'temperature',
                'name': '温度传感器',
                'unit': '°C',
                'description': '监测环境温度',
                'is_required': True,
                'validation_rules': {'min': -30, 'max': 70}
            },
            {
                'type': 'humidity',
                'name': '湿度传感器',
                'unit': '%',
                'description': '监测空气湿度',
                'is_required': True,
                'validation_rules': {'min': 0, 'max': 100}
            },
            {
                'type': 'co2',
                'name': 'CO2传感器',
                'unit': 'ppm',
                'description': '监测二氧化碳浓度',
                'is_required': True,
                'validation_rules': {'min': 0, 'max': 5000}
            },
            {
                'type': 'noise',
                'name': '噪音传感器',
                'unit': 'dB',
                'description': '监测环境噪音',
                'is_required': False,
                'validation_rules': {'min': 0, 'max': 120}
            },
            {
                'type': 'light',
                'name': '光照传感器',
                'unit': 'lux',
                'description': '监测光照强度',
                'is_required': False,
                'validation_rules': {'min': 0, 'max': 2000}
            }
        ],
        'default_config': {
            'collection_interval': 15,
            'data_retention_days': 180,
            'alert_enabled': True
        }
    },
    {
        'device_type': 'water_management',
        'name': '水管理设备',
        'description': '水质监测和灌溉控制设备',
        'manufacturer': 'AgriNex',
        'model': 'WM-2024',
        'sensor_configs': [
            {
                'type': 'water_level',
                'name': '水位传感器',
                'unit': '%',
                'description': '监测水位高度',
                'is_required': True,
                'validation_rules': {'min': 0, 'max': 100}
            },
            {
                'type': 'flow_rate',
                'name': '流量传感器',
                'unit': 'L/min',
                'description': '监测水流速度',
                'is_required': True,
                'validation_rules': {'min': 0, 'max': 100}
            },
            {
                'type': 'pressure',
                'name': '水压传感器',
                'unit': 'bar',
                'description': '监测水压',
                'is_required': True,
                'validation_rules': {'min': 0, 'max': 20}
            },
            {
                'type': 'temperature',
                'name': '水温传感器',
                'unit': '°C',
                'description': '监测水温',
                'is_required': False,
                'validation_rules': {'min': 0, 'max': 50}
            }
        ],
        'default_config': {
            'collection_interval': 20,
            'data_retention_days': 365,
            'alert_enabled': True
        }
    }
]


# 完整的传感器类型定义
SENSOR_TYPES = {
    # 基础环境传感器
    'temperature': {'name': '温度传感器', 'unit': '°C', 'category': 'environment'},
    'humidity': {'name': '湿度传感器', 'unit': '%', 'category': 'environment'},
    'pressure': {'name': '压力传感器', 'unit': 'hPa', 'category': 'environment'},
    'light': {'name': '光照传感器', 'unit': 'lux', 'category': 'environment'},
    'co2': {'name': 'CO2传感器', 'unit': 'ppm', 'category': 'environment'},
    'noise': {'name': '噪音传感器', 'unit': 'dB', 'category': 'environment'},
    
    # 土壤传感器
    'soil_moisture': {'name': '土壤湿度传感器', 'unit': '%', 'category': 'soil'},
    'soil_temperature': {'name': '土壤温度传感器', 'unit': '°C', 'category': 'soil'},
    'soil_ph': {'name': '土壤pH传感器', 'unit': 'pH', 'category': 'soil'},
    'soil_ec': {'name': '土壤电导率传感器', 'unit': 'mS/cm', 'category': 'soil'},
    'soil_npk': {'name': '土壤NPK传感器', 'unit': 'mg/kg', 'category': 'soil'},
    'soil_organic': {'name': '土壤有机质传感器', 'unit': '%', 'category': 'soil'},
    
    # 水质传感器
    'water_level': {'name': '水位传感器', 'unit': '%', 'category': 'water'},
    'water_temperature': {'name': '水温传感器', 'unit': '°C', 'category': 'water'},
    'water_ph': {'name': '水体pH传感器', 'unit': 'pH', 'category': 'water'},
    'dissolved_oxygen': {'name': '溶解氧传感器', 'unit': 'mg/L', 'category': 'water'},
    'turbidity': {'name': '浊度传感器', 'unit': 'NTU', 'category': 'water'},
    'salinity': {'name': '盐度传感器', 'unit': 'ppt', 'category': 'water'},
    'water_quality': {'name': '水质传感器', 'unit': 'TDS', 'category': 'water'},
    
    # 气象传感器
    'wind_speed': {'name': '风速传感器', 'unit': 'm/s', 'category': 'weather'},
    'wind_direction': {'name': '风向传感器', 'unit': '°', 'category': 'weather'},
    'rain_level': {'name': '雨量传感器', 'unit': 'mm', 'category': 'weather'},
    'uv_index': {'name': 'UV指数传感器', 'unit': 'UV', 'category': 'weather'},
    
    # 流量传感器
    'flow_rate': {'name': '流量传感器', 'unit': 'L/min', 'category': 'flow'},
    
    # 空气质量传感器
    'air_quality': {'name': '空气质量传感器', 'unit': 'AQI', 'category': 'air_quality'},
    'ammonia': {'name': '氨气传感器', 'unit': 'ppm', 'category': 'air_quality'},
    
    # 运动和状态传感器
    'motion': {'name': '运动传感器', 'unit': 'count', 'category': 'motion'},
    'valve_status': {'name': '阀门状态传感器', 'unit': 'status', 'category': 'control'},
    'pump_status': {'name': '水泵状态传感器', 'unit': 'rpm', 'category': 'control'},
    'door_sensor': {'name': '门禁传感器', 'unit': 'status', 'category': 'security'},
    
    # 害虫检测
    'pest_detection': {'name': '害虫检测传感器', 'unit': 'count', 'category': 'pest'},
    
    # 无人机专用传感器
    'multispectral': {'name': '多光谱传感器', 'unit': 'index', 'category': 'drone'},
    'thermal': {'name': '热红外传感器', 'unit': '°C', 'category': 'drone'},
    'altitude': {'name': '高度传感器', 'unit': 'm', 'category': 'drone'},
    'gps_accuracy': {'name': 'GPS精度传感器', 'unit': 'm', 'category': 'drone'},
    'battery_level': {'name': '电池电量传感器', 'unit': '%', 'category': 'power'},
    'wind_resistance': {'name': '抗风能力传感器', 'unit': 'm/s', 'category': 'drone'}
}

DEVICE_CATEGORIES = {
    'basic': '基础设备',
    'greenhouse': '温室设备',
    'field': '田间设备',
    'livestock': '畜牧设备',
    'aquaculture': '水产设备',
    'storage': '仓储设备',
    'mobile': '移动设备',
    'control': '控制设备'
}


def init_device_templates():
    """初始化预定义设备模板"""
    for template_data in PREDEFINED_DEVICE_TEMPLATES:
        existing = DeviceTemplate.query.filter_by(
            device_type=template_data['device_type']
        ).first()
        
        if not existing:
            template = DeviceTemplate.create_with_sensors(**template_data)
            print(f"Created device template: {template.name}")
        else:
            print(f"Device template already exists: {existing.name}")
    
    try:
        db.session.commit()
        print("Device templates initialization completed.")
    except Exception as e:
        db.session.rollback()
        print(f"Error initializing device templates: {e}")
        raise
