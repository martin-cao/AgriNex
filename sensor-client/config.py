# sensor-client/config.py
import os
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class SensorConfig:
    """传感器配置类"""
    # 客户端基本信息
    client_id: str = "sensor_001"
    
    # MQTT配置
    mqtt_host: str = "localhost"
    mqtt_port: int = 1883
    mqtt_username: str = ""
    mqtt_password: str = ""
    mqtt_keepalive: int = 60
    
    # 串口配置
    serial_port: str = ""  # 自动检测
    serial_baudrate: int = 9600
    serial_timeout: float = 1.0
    
    # 摄像头配置
    camera_device_id: int = 0
    camera_width: int = 640
    camera_height: int = 480
    camera_fps: int = 20
    
    # 数据采集间隔
    numeric_interval: float = 10.0  # 数值数据采集间隔(秒)
    image_interval: float = 60.0    # 图像数据采集间隔(秒)
    
    # 视频录制配置
    video_duration: int = 5         # 视频录制时长(秒)
    video_codec: str = "XVID"       # 视频编码格式
    video_quality: int = 90         # 视频质量(0-100)
    
    # 数据处理配置
    temperature_offset: float = 0.0
    humidity_offset: float = 0.0
    light_offset: float = 0.0
    
    @classmethod
    def from_env(cls) -> 'SensorConfig':
        """从环境变量加载配置"""
        return cls(
            client_id=os.getenv('SENSOR_CLIENT_ID', 'sensor_001'),
            
            mqtt_host=os.getenv('MQTT_HOST', 'localhost'),
            mqtt_port=int(os.getenv('MQTT_PORT', '1883')),
            mqtt_username=os.getenv('MQTT_USERNAME', ''),
            mqtt_password=os.getenv('MQTT_PASSWORD', ''),
            mqtt_keepalive=int(os.getenv('MQTT_KEEPALIVE', '60')),
            
            serial_port=os.getenv('SERIAL_PORT', ''),
            serial_baudrate=int(os.getenv('SERIAL_BAUDRATE', '9600')),
            serial_timeout=float(os.getenv('SERIAL_TIMEOUT', '1.0')),
            
            camera_device_id=int(os.getenv('CAMERA_DEVICE_ID', '0')),
            camera_width=int(os.getenv('CAMERA_WIDTH', '640')),
            camera_height=int(os.getenv('CAMERA_HEIGHT', '480')),
            camera_fps=int(os.getenv('CAMERA_FPS', '20')),
            
            numeric_interval=float(os.getenv('NUMERIC_INTERVAL', '10.0')),
            image_interval=float(os.getenv('IMAGE_INTERVAL', '60.0')),
            
            video_duration=int(os.getenv('VIDEO_DURATION', '5')),
            video_codec=os.getenv('VIDEO_CODEC', 'XVID'),
            video_quality=int(os.getenv('VIDEO_QUALITY', '90')),
            
            temperature_offset=float(os.getenv('TEMPERATURE_OFFSET', '0.0')),
            humidity_offset=float(os.getenv('HUMIDITY_OFFSET', '0.0')),
            light_offset=float(os.getenv('LIGHT_OFFSET', '0.0')),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'client_id': self.client_id,
            'mqtt': {
                'host': self.mqtt_host,
                'port': self.mqtt_port,
                'username': self.mqtt_username,
                'password': self.mqtt_password,
                'keepalive': self.mqtt_keepalive
            },
            'serial': {
                'port': self.serial_port,
                'baudrate': self.serial_baudrate,
                'timeout': self.serial_timeout
            },
            'camera': {
                'device_id': self.camera_device_id,
                'width': self.camera_width,
                'height': self.camera_height,
                'fps': self.camera_fps
            },
            'intervals': {
                'numeric': self.numeric_interval,
                'image': self.image_interval
            },
            'video': {
                'duration': self.video_duration,
                'codec': self.video_codec,
                'quality': self.video_quality
            },
            'offsets': {
                'temperature': self.temperature_offset,
                'humidity': self.humidity_offset,
                'light': self.light_offset
            }
        }
