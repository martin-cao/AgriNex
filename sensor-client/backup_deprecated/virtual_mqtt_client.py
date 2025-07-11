#!/usr/bin/env python3
"""
支持虚拟串口的MQTT传感器客户端
"""

import asyncio
import json
import logging
import os
import sys
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
import base64
import hashlib

import paho.mqtt.client as mqtt
import cv2
import numpy as np

# 导入串口模拟器
from serial_simulator import SerialDeviceManager, VirtualSerialPort

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VirtualSerialConnector:
    """虚拟串口连接器"""
    
    def __init__(self, device_manager: SerialDeviceManager):
        self.device_manager = device_manager
        self.current_port = None
        self.port_name = None
        self.is_connected = False
    
    def scan_ports(self) -> List[str]:
        """扫描可用的虚拟串口"""
        ports = self.device_manager.list_ports()
        logger.info(f"发现虚拟串口: {ports}")
        return ports
    
    def connect(self, port_name: Optional[str] = None) -> bool:
        """连接虚拟串口"""
        try:
            if port_name:
                self.port_name = port_name
            
            if not self.port_name:
                # 自动选择第一个可用串口
                available_ports = self.scan_ports()
                if available_ports:
                    self.port_name = available_ports[0]
                else:
                    logger.error("未找到可用的虚拟串口")
                    return False
            
            self.current_port = self.device_manager.get_port(self.port_name)
            if not self.current_port:
                logger.error(f"虚拟串口 {self.port_name} 不存在")
                return False
            
            self.current_port.open()
            self.is_connected = True
            logger.info(f"虚拟串口连接成功: {self.port_name}")
            return True
            
        except Exception as e:
            logger.error(f"虚拟串口连接失败: {e}")
            return False
    
    def read_data(self, timeout: float = 5.0) -> Optional[bytes]:
        """读取虚拟串口数据"""
        if not self.is_connected or not self.current_port:
            return None
        
        try:
            # 设置超时
            self.current_port.timeout = timeout
            data = self.current_port.readline()
            return data if data else None
            
        except Exception as e:
            logger.error(f"虚拟串口读取失败: {e}")
            return None
    
    def close(self):
        """关闭虚拟串口连接"""
        if self.current_port:
            self.current_port.close()
            self.is_connected = False
            logger.info("虚拟串口连接已关闭")


class EnhancedMQTTSensorClient:
    """增强的MQTT传感器客户端，支持虚拟串口"""
    
    def __init__(self, client_id: str, mqtt_config: Dict[str, Any], device_manager: SerialDeviceManager):
        self.client_id = client_id
        self.mqtt_config = mqtt_config
        self.device_manager = device_manager
        self.client = None
        self.is_connected = False
        
        # 使用虚拟串口连接器
        self.serial_connector = VirtualSerialConnector(device_manager)
        
        # 运行配置
        self.running = False
        self.numeric_interval = 10.0  # 数值数据采集间隔(秒)
        self.image_interval = 60.0    # 图像数据采集间隔(秒)
        
        # 数据处理器
        self.data_processor = SensorDataProcessor()
        
        # 摄像头连接器（可选）
        self.camera_connector = None
        try:
            self.camera_connector = CameraConnector()
        except Exception as e:
            logger.warning(f"摄像头初始化失败: {e}")
    
    def on_connect(self, client, userdata, flags, rc):
        """MQTT连接回调"""
        if rc == 0:
            self.is_connected = True
            logger.info(f"MQTT连接成功: {self.client_id}")
            
            # 订阅控制主题
            control_topic = f"control/{self.client_id}/+"
            client.subscribe(control_topic)
            logger.info(f"订阅控制主题: {control_topic}")
            
        else:
            logger.error(f"MQTT连接失败: {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        """MQTT断开连接回调"""
        self.is_connected = False
        logger.info(f"MQTT连接断开: {rc}")
    
    def on_message(self, client, userdata, msg):
        """消息接收回调"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            
            logger.info(f"收到控制消息: {topic} -> {payload}")
            
            # 处理控制命令
            if topic.endswith('/config'):
                self.handle_config_command(payload)
            elif topic.endswith('/capture'):
                self.handle_capture_command(payload)
                
        except Exception as e:
            logger.error(f"消息处理失败: {e}")
    
    def handle_config_command(self, payload: Dict[str, Any]):
        """处理配置命令"""
        try:
            if 'numeric_interval' in payload:
                self.numeric_interval = float(payload['numeric_interval'])
                logger.info(f"数值采集间隔更新为: {self.numeric_interval}s")
            
            if 'image_interval' in payload:
                self.image_interval = float(payload['image_interval'])
                logger.info(f"图像采集间隔更新为: {self.image_interval}s")
                
        except Exception as e:
            logger.error(f"配置命令处理失败: {e}")
    
    def handle_capture_command(self, payload: Dict[str, Any]):
        """处理捕获命令"""
        try:
            data_type = payload.get('type', 'image')
            
            if data_type == 'image':
                asyncio.create_task(self.capture_and_send_image())
            elif data_type == 'video':
                asyncio.create_task(self.capture_and_send_video())
                
        except Exception as e:
            logger.error(f"捕获命令处理失败: {e}")
    
    def connect_mqtt(self) -> bool:
        """连接MQTT服务器"""
        try:
            self.client = mqtt.Client(client_id=self.client_id)
            
            # 设置回调
            self.client.on_connect = self.on_connect
            self.client.on_disconnect = self.on_disconnect
            self.client.on_message = self.on_message
            
            # 设置认证
            if self.mqtt_config.get('username') and self.mqtt_config.get('password'):
                self.client.username_pw_set(
                    self.mqtt_config['username'],
                    self.mqtt_config['password']
                )
            
            # 连接服务器
            self.client.connect(
                self.mqtt_config['host'],
                self.mqtt_config['port'],
                self.mqtt_config.get('keepalive', 60)
            )
            
            # 启动网络循环
            self.client.loop_start()
            
            return True
            
        except Exception as e:
            logger.error(f"MQTT连接失败: {e}")
            return False
    
    def publish_data(self, topic: str, data: Dict[str, Any], qos: int = 1) -> bool:
        """发布数据到MQTT"""
        if not self.is_connected or not self.client:
            logger.error("MQTT未连接")
            return False
        
        try:
            # 添加时间戳和客户端ID
            data.update({
                'timestamp': datetime.utcnow().isoformat(),
                'client_id': self.client_id
            })
            
            payload = json.dumps(data, ensure_ascii=False)
            result = self.client.publish(topic, payload, qos=qos)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"数据发布成功: {topic}")
                return True
            else:
                logger.error(f"数据发布失败: {result.rc}")
                return False
                
        except Exception as e:
            logger.error(f"数据发布异常: {e}")
            return False
    
    async def collect_numeric_data(self):
        """采集数值传感器数据"""
        while self.running:
            try:
                if self.serial_connector.is_connected:
                    # 从虚拟串口读取数据
                    raw_data = self.serial_connector.read_data()
                    if raw_data:
                        data_str = raw_data.decode('utf-8').strip()
                        logger.info(f"从虚拟串口读取数据: {data_str}")
                        
                        processed_data = self.data_processor.process_numeric_data(data_str)
                        
                        if processed_data:
                            # 发布到MQTT
                            topic = f"sensors/{self.client_id}/numeric"
                            mqtt_data = {
                                'type': 'numeric',
                                'data': processed_data,
                                'source': 'virtual_serial'
                            }
                            self.publish_data(topic, mqtt_data)
                        else:
                            logger.warning(f"数据处理失败: {data_str}")
                else:
                    logger.warning("虚拟串口未连接")
                
                await asyncio.sleep(self.numeric_interval)
                
            except Exception as e:
                logger.error(f"数值数据采集失败: {e}")
                await asyncio.sleep(5.0)
    
    async def capture_and_send_image(self):
        """捕获并发送图像数据"""
        try:
            if not self.camera_connector or not self.camera_connector.is_connected:
                logger.warning("摄像头未连接，生成模拟图像数据")
                
                # 生成模拟图像数据
                fake_image = b'fake_image_data_' + str(int(time.time())).encode()
                processed_data = {
                    'data': base64.b64encode(fake_image).decode('utf-8'),
                    'format': 'jpg',
                    'size': len(fake_image),
                    'hash': hashlib.md5(fake_image).hexdigest(),
                    'encoding': 'base64'
                }
            else:
                # 捕获真实图像
                image_data = self.camera_connector.capture_image('jpg')
                if image_data:
                    processed_data = self.data_processor.process_image_data(image_data, 'jpg')
                else:
                    logger.error("图像捕获失败")
                    return
            
            if processed_data:
                # 发布到MQTT
                topic = f"sensors/{self.client_id}/image"
                mqtt_data = {
                    'type': 'image',
                    'data': processed_data,
                    'source': 'camera' if self.camera_connector and self.camera_connector.is_connected else 'simulated'
                }
                self.publish_data(topic, mqtt_data)
                
        except Exception as e:
            logger.error(f"图像数据捕获失败: {e}")
    
    async def capture_and_send_video(self):
        """捕获并发送视频数据"""
        try:
            logger.info("生成模拟视频数据")
            
            # 生成模拟视频数据
            fake_video = b'fake_video_data_' + str(int(time.time())).encode()
            processed_data = {
                'data': base64.b64encode(fake_video).decode('utf-8'),
                'format': 'avi',
                'size': len(fake_video),
                'hash': hashlib.md5(fake_video).hexdigest(),
                'encoding': 'base64',
                'duration': 5,
                'fps': 20,
                'resolution': '640x480'
            }
            
            if processed_data:
                # 发布到MQTT
                topic = f"sensors/{self.client_id}/video"
                mqtt_data = {
                    'type': 'video',
                    'data': processed_data,
                    'source': 'simulated'
                }
                self.publish_data(topic, mqtt_data)
                
        except Exception as e:
            logger.error(f"视频数据捕获失败: {e}")
    
    async def collect_image_data(self):
        """定期采集图像数据"""
        while self.running:
            try:
                await self.capture_and_send_image()
                await asyncio.sleep(self.image_interval)
                
            except Exception as e:
                logger.error(f"图像数据采集失败: {e}")
                await asyncio.sleep(10.0)
    
    async def start(self, port_name: Optional[str] = None):
        """启动传感器客户端"""
        logger.info("启动增强的传感器客户端...")
        
        # 连接MQTT
        if not self.connect_mqtt():
            logger.error("MQTT连接失败")
            return
        
        # 等待MQTT连接
        await asyncio.sleep(2.0)
        
        # 连接虚拟串口
        if not self.serial_connector.connect(port_name):
            logger.error("虚拟串口连接失败")
            return
        
        # 连接摄像头（可选）
        if self.camera_connector and not self.camera_connector.connect():
            logger.warning("摄像头连接失败，将生成模拟图像数据")
        
        # 启动数据采集任务
        self.running = True
        
        tasks = [
            asyncio.create_task(self.collect_numeric_data()),
            asyncio.create_task(self.collect_image_data())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            logger.info("接收到停止信号")
        finally:
            await self.stop()
    
    async def stop(self):
        """停止传感器客户端"""
        logger.info("停止传感器客户端...")
        
        self.running = False
        
        # 关闭连接
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
        
        self.serial_connector.close()
        
        if self.camera_connector:
            self.camera_connector.close()
        
        logger.info("传感器客户端已停止")


# 导入必要的类
from serial_simulator import SerialDeviceManager, EnvironmentSensorDevice, TemperatureSensorDevice, create_demo_devices

class SensorDataProcessor:
    """传感器数据处理器"""
    
    def __init__(self):
        self.temperature_offset = 0.0
        self.humidity_offset = 0.0
        self.light_offset = 0.0
    
    def process_numeric_data(self, raw_data: str) -> Dict[str, Any]:
        """处理数值型传感器数据"""
        try:
            # 解析串口数据格式: "T:25.5,H:60.2,L:1200.0"
            parts = raw_data.strip().split(',')
            data = {}
            
            for part in parts:
                if ':' in part:
                    key, value = part.split(':', 1)
                    key = key.strip()
                    value = float(value.strip())
                    
                    if key == 'T':
                        data['temperature'] = value + self.temperature_offset
                        data['temperature_unit'] = '°C'
                    elif key == 'H':
                        data['humidity'] = value + self.humidity_offset
                        data['humidity_unit'] = '%'
                    elif key == 'L':
                        data['light'] = value + self.light_offset
                        data['light_unit'] = 'lux'
                    elif key == 'SM':
                        data['soil_moisture'] = value
                        data['soil_moisture_unit'] = '%'
                    elif key == 'PH':
                        data['soil_ph'] = value
                        data['soil_ph_unit'] = 'pH'
                    elif key == 'EC':
                        data['soil_ec'] = value
                        data['soil_ec_unit'] = 'mS/cm'
                    elif key == 'P':
                        data['pressure'] = value
                        data['pressure_unit'] = 'hPa'
                    elif key == 'W':
                        data['wind_speed'] = value
                        data['wind_speed_unit'] = 'm/s'
            
            return data
        except Exception as e:
            logger.error(f"数值数据处理失败: {e}")
            return {}
    
    def process_image_data(self, image_data: bytes, format_type: str = 'jpg') -> Dict[str, Any]:
        """处理图像数据"""
        try:
            # 计算文件哈希
            file_hash = hashlib.md5(image_data).hexdigest()
            
            # 编码为base64
            encoded_data = base64.b64encode(image_data).decode('utf-8')
            
            return {
                'data': encoded_data,
                'format': format_type,
                'size': len(image_data),
                'hash': file_hash,
                'encoding': 'base64'
            }
        except Exception as e:
            logger.error(f"图像数据处理失败: {e}")
            return {}


class CameraConnector:
    """摄像头连接器"""
    
    def __init__(self, device_id: int = 0):
        self.device_id = device_id
        self.cap = None
        self.is_connected = False
    
    def connect(self) -> bool:
        """连接摄像头"""
        try:
            self.cap = cv2.VideoCapture(self.device_id)
            if self.cap.isOpened():
                self.is_connected = True
                logger.info(f"摄像头连接成功: {self.device_id}")
                return True
            else:
                logger.error(f"摄像头连接失败: {self.device_id}")
                return False
                
        except Exception as e:
            logger.error(f"摄像头连接异常: {e}")
            return False
    
    def capture_image(self, format_type: str = 'jpg') -> Optional[bytes]:
        """捕获图像"""
        if not self.is_connected or not self.cap:
            return None
        
        try:
            ret, frame = self.cap.read()
            if ret:
                # 编码图像
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
                result, encoded_img = cv2.imencode(f'.{format_type}', frame, encode_param)
                
                if result:
                    return encoded_img.tobytes()
            
            return None
            
        except Exception as e:
            logger.error(f"图像捕获失败: {e}")
            return None
    
    def close(self):
        """关闭摄像头"""
        if self.cap:
            self.cap.release()
            self.is_connected = False
            logger.info("摄像头连接已关闭")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='支持虚拟串口的MQTT传感器客户端')
    parser.add_argument('--client-id', default=f'sensor_{uuid.uuid4().hex[:8]}', help='客户端ID')
    parser.add_argument('--mqtt-host', default='localhost', help='MQTT服务器地址')
    parser.add_argument('--mqtt-port', type=int, default=1883, help='MQTT服务器端口')
    parser.add_argument('--port', help='指定虚拟串口名称')
    parser.add_argument('--interval', type=float, default=10.0, help='数据采集间隔')
    parser.add_argument('--device-interval', type=float, default=5.0, help='设备数据生成间隔')
    
    args = parser.parse_args()
    
    # 创建设备管理器和演示设备
    logger.info("创建虚拟串口设备...")
    device_manager = SerialDeviceManager()
    create_demo_devices(device_manager)
    
    # 设置设备数据生成间隔
    for device_id in device_manager.devices:
        device_manager.set_device_interval(device_id, args.device_interval)
    
    # 启动虚拟设备
    device_manager.start_all_devices()
    
    # 配置MQTT
    mqtt_config = {
        'host': args.mqtt_host,
        'port': args.mqtt_port,
        'username': os.getenv('MQTT_USERNAME', ''),
        'password': os.getenv('MQTT_PASSWORD', ''),
        'keepalive': int(os.getenv('MQTT_KEEPALIVE', '60'))
    }
    
    # 创建MQTT客户端
    client = EnhancedMQTTSensorClient(args.client_id, mqtt_config, device_manager)
    
    # 启动客户端
    try:
        asyncio.run(client.start(args.port))
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.error(f"程序运行异常: {e}")
    finally:
        # 停止虚拟设备
        device_manager.stop_all_devices()


if __name__ == "__main__":
    main()
