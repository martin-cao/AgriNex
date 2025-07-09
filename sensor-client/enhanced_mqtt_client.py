#!/usr/bin/env python3
"""
增强的MQTT传感器客户端
支持多种数据格式和传感器类型
"""

import asyncio
import json
import logging
import os
import sys
import time
import uuid
import base64
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
import threading
import queue

import paho.mqtt.client as mqtt
import cv2
import numpy as np

# 导入增强的串口模拟器
from enhanced_serial_simulator import (
    EnhancedSerialDeviceManager, 
    DataFormat, 
    SensorType,
    create_comprehensive_demo_setup
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EnhancedSerialDataProcessor:
    """增强的串口数据处理器"""
    
    def __init__(self):
        self.format_processors = {
            DataFormat.JSON: self._process_json,
            DataFormat.CSV: self._process_csv,
            DataFormat.BINARY: self._process_binary,
            DataFormat.CUSTOM: self._process_custom
        }
    
    def process_data(self, raw_data: bytes, format_type: DataFormat = DataFormat.CSV) -> Dict[str, Any]:
        """处理原始数据"""
        try:
            processor = self.format_processors.get(format_type, self._process_csv)
            return processor(raw_data)
        except Exception as e:
            logger.error(f"数据处理失败: {e}")
            return {}
    
    def _process_json(self, raw_data: bytes) -> Dict[str, Any]:
        """处理JSON格式数据"""
        try:
            data_str = raw_data.decode('utf-8').strip()
            data = json.loads(data_str)
            
            # 转换为统一格式
            processed = {
                'device_id': data.get('device_id', 'unknown'),
                'timestamp': data.get('timestamp', datetime.now().isoformat()),
                'sensors': {},
                'device_status': data.get('device_status', {}),
                'format': 'json'
            }
            
            # 处理传感器读数
            for reading in data.get('readings', []):
                sensor_type = reading.get('sensor_type', 'unknown')
                sensor_id = reading.get('sensor_id', 'unknown')
                value = reading.get('value', 0)
                unit = reading.get('unit', '')
                quality = reading.get('quality', 1.0)
                
                processed['sensors'][sensor_id] = {
                    'type': sensor_type,
                    'value': value,
                    'unit': unit,
                    'quality': quality
                }
            
            return processed
            
        except Exception as e:
            logger.error(f"JSON数据处理失败: {e}")
            return {}
    
    def _process_csv(self, raw_data: bytes) -> Dict[str, Any]:
        """处理CSV格式数据"""
        try:
            data_str = raw_data.decode('utf-8').strip()
            lines = data_str.split('\n')
            
            processed = {
                'device_id': 'unknown',
                'timestamp': datetime.now().isoformat(),
                'sensors': {},
                'device_status': {},
                'format': 'csv'
            }
            
            for line in lines:
                if not line.strip():
                    continue
                    
                # CSV格式: device_id,timestamp,sensor_id,sensor_type,value,unit,quality
                parts = line.split(',')
                if len(parts) >= 6:
                    device_id = parts[0]
                    timestamp = parts[1]
                    sensor_id = parts[2]
                    sensor_type = parts[3]
                    value = float(parts[4])
                    unit = parts[5]
                    quality = float(parts[6]) if len(parts) > 6 else 1.0
                    
                    processed['device_id'] = device_id
                    processed['timestamp'] = timestamp
                    processed['sensors'][sensor_id] = {
                        'type': sensor_type,
                        'value': value,
                        'unit': unit,
                        'quality': quality
                    }
            
            return processed
            
        except Exception as e:
            logger.error(f"CSV数据处理失败: {e}")
            return {}
    
    def _process_binary(self, raw_data: bytes) -> Dict[str, Any]:
        """处理二进制格式数据"""
        try:
            import struct
            
            if len(raw_data) < 8:
                return {}
            
            # 解析头部
            reading_count = struct.unpack('!I', raw_data[0:4])[0]
            timestamp = struct.unpack('!I', raw_data[4:8])[0]
            
            processed = {
                'device_id': 'binary_device',
                'timestamp': datetime.fromtimestamp(timestamp).isoformat(),
                'sensors': {},
                'device_status': {},
                'format': 'binary'
            }
            
            # 解析传感器数据
            offset = 8
            for i in range(reading_count):
                if offset + 24 > len(raw_data):
                    break
                
                # 传感器ID (16字节)
                sensor_id = raw_data[offset:offset+16].decode('utf-8').rstrip('\0')
                offset += 16
                
                # 值 (4字节浮点数)
                value = struct.unpack('!f', raw_data[offset:offset+4])[0]
                offset += 4
                
                # 质量 (4字节浮点数)
                quality = struct.unpack('!f', raw_data[offset:offset+4])[0]
                offset += 4
                
                processed['sensors'][sensor_id] = {
                    'type': 'unknown',
                    'value': value,
                    'unit': '',
                    'quality': quality
                }
            
            return processed
            
        except Exception as e:
            logger.error(f"二进制数据处理失败: {e}")
            return {}
    
    def _process_custom(self, raw_data: bytes) -> Dict[str, Any]:
        """处理自定义格式数据"""
        try:
            data_str = raw_data.decode('utf-8').strip()
            
            processed = {
                'device_id': 'unknown',
                'timestamp': datetime.now().isoformat(),
                'sensors': {},
                'device_status': {},
                'format': 'custom'
            }
            
            # 自定义格式: DEV_ID:SENSOR_TYPE:VALUE:UNIT;
            parts = data_str.rstrip(';').split(';')
            
            for part in parts:
                if ':' not in part:
                    continue
                
                elements = part.split(':')
                if len(elements) >= 4:
                    device_id = elements[0]
                    sensor_type = elements[1]
                    value = float(elements[2])
                    unit = elements[3]
                    
                    processed['device_id'] = device_id
                    sensor_id = f"{sensor_type}_sensor"
                    
                    processed['sensors'][sensor_id] = {
                        'type': sensor_type,
                        'value': value,
                        'unit': unit,
                        'quality': 1.0
                    }
            
            return processed
            
        except Exception as e:
            logger.error(f"自定义数据处理失败: {e}")
            return {}


class EnhancedMQTTSensorClient:
    """增强的MQTT传感器客户端"""
    
    def __init__(self, client_id: str, mqtt_config: Dict[str, Any]):
        self.client_id = client_id
        self.mqtt_config = mqtt_config
        self.client = None
        self.is_connected = False
        
        # 设备管理器
        self.device_manager = EnhancedSerialDeviceManager()
        
        # 数据处理器
        self.data_processor = EnhancedSerialDataProcessor()
        
        # 运行配置
        self.running = False
        self.active_connections = {}  # 活跃的串口连接
        
        # 配置
        self.scan_interval = 5.0  # 串口扫描间隔
        self.retry_interval = 10.0  # 重连间隔
        self.max_retries = 3
        
        # 统计信息
        self.total_messages = 0
        self.error_count = 0
        self.start_time = None
        
        # 摄像头支持
        self.camera_enabled = False
        self.camera_cap = None
        self.image_interval = 60.0
        
    def on_connect(self, client, userdata, flags, rc):
        """MQTT连接回调"""
        if rc == 0:
            self.is_connected = True
            logger.info(f"MQTT连接成功: {self.client_id}")
            
            # 订阅控制主题
            control_topics = [
                f"control/{self.client_id}/config",
                f"control/{self.client_id}/scan",
                f"control/{self.client_id}/capture",
                f"control/{self.client_id}/status"
            ]
            
            for topic in control_topics:
                client.subscribe(topic)
                logger.info(f"订阅控制主题: {topic}")
            
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
            
            logger.info(f"收到控制消息: {topic}")
            
            # 处理控制命令
            if topic.endswith('/config'):
                self.handle_config_command(payload)
            elif topic.endswith('/scan'):
                self.handle_scan_command(payload)
            elif topic.endswith('/capture'):
                self.handle_capture_command(payload)
            elif topic.endswith('/status'):
                self.handle_status_command(payload)
                
        except Exception as e:
            logger.error(f"消息处理失败: {e}")
    
    def handle_config_command(self, payload: Dict[str, Any]):
        """处理配置命令"""
        try:
            if 'scan_interval' in payload:
                self.scan_interval = float(payload['scan_interval'])
                logger.info(f"扫描间隔更新为: {self.scan_interval}s")
            
            if 'image_interval' in payload:
                self.image_interval = float(payload['image_interval'])
                logger.info(f"图像采集间隔更新为: {self.image_interval}s")
            
            if 'camera_enabled' in payload:
                self.camera_enabled = bool(payload['camera_enabled'])
                logger.info(f"摄像头支持: {'启用' if self.camera_enabled else '禁用'}")
                
        except Exception as e:
            logger.error(f"配置命令处理失败: {e}")
    
    def handle_scan_command(self, payload: Dict[str, Any]):
        """处理扫描命令"""
        try:
            # 手动触发串口扫描
            asyncio.create_task(self.scan_and_connect_ports())
            
            # 发送响应
            response = {
                'command': 'scan',
                'status': 'started',
                'timestamp': datetime.now().isoformat()
            }
            
            self.publish_response('scan', response)
            
        except Exception as e:
            logger.error(f"扫描命令处理失败: {e}")
    
    def handle_capture_command(self, payload: Dict[str, Any]):
        """处理捕获命令"""
        try:
            data_type = payload.get('type', 'image')
            
            if data_type == 'image':
                asyncio.create_task(self.capture_and_send_image())
            elif data_type == 'video':
                asyncio.create_task(self.capture_and_send_video())
            elif data_type == 'snapshot':
                asyncio.create_task(self.capture_sensor_snapshot())
                
        except Exception as e:
            logger.error(f"捕获命令处理失败: {e}")
    
    def handle_status_command(self, payload: Dict[str, Any]):
        """处理状态命令"""
        try:
            # 获取系统状态
            stats = self.get_system_stats()
            
            # 发送状态响应
            self.publish_response('status', stats)
            
        except Exception as e:
            logger.error(f"状态命令处理失败: {e}")
    
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
            # 添加元数据
            data.update({
                'mqtt_timestamp': datetime.utcnow().isoformat(),
                'client_id': self.client_id,
                'message_id': str(uuid.uuid4())
            })
            
            payload = json.dumps(data, ensure_ascii=False)
            result = self.client.publish(topic, payload, qos=qos)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                self.total_messages += 1
                logger.debug(f"数据发布成功: {topic}")
                return True
            else:
                logger.error(f"数据发布失败: {result.rc}")
                return False
                
        except Exception as e:
            logger.error(f"数据发布异常: {e}")
            return False
    
    def publish_response(self, command: str, response: Dict[str, Any]):
        """发布响应消息"""
        topic = f"response/{self.client_id}/{command}"
        self.publish_data(topic, response)
    
    async def scan_and_connect_ports(self):
        """扫描并连接串口"""
        try:
            logger.info("开始扫描虚拟串口...")
            
            # 获取可用端口
            available_ports = self.device_manager.list_ports()
            
            for port_name in available_ports:
                if port_name not in self.active_connections:
                    logger.info(f"尝试连接端口: {port_name}")
                    
                    # 获取端口对象
                    port = self.device_manager.get_port(port_name)
                    if port and not port.is_open:
                        port.open()
                        self.active_connections[port_name] = {
                            'port': port,
                            'last_data': None,
                            'error_count': 0,
                            'connected_time': datetime.now()
                        }
                        logger.info(f"成功连接端口: {port_name}")
            
            logger.info(f"当前活跃连接数: {len(self.active_connections)}")
            
        except Exception as e:
            logger.error(f"端口扫描失败: {e}")
    
    async def collect_sensor_data(self):
        """采集传感器数据"""
        while self.running:
            try:
                # 从所有活跃连接读取数据
                for port_name, connection in list(self.active_connections.items()):
                    try:
                        port = connection['port']
                        
                        # 读取数据
                        raw_data = port.read(1024)  # 读取最多1024字节
                        
                        if raw_data:
                            # 尝试按行处理
                            if b'\\n' in raw_data:
                                lines = raw_data.split(b'\\n')
                                for line in lines:
                                    if line.strip():
                                        await self.process_sensor_line(port_name, line.strip())
                            else:
                                await self.process_sensor_line(port_name, raw_data)
                        
                        # 重置错误计数
                        connection['error_count'] = 0
                        
                    except Exception as e:
                        connection['error_count'] += 1
                        logger.error(f"端口 {port_name} 数据读取失败: {e}")
                        
                        # 如果错误次数过多，断开连接
                        if connection['error_count'] > self.max_retries:
                            logger.warning(f"端口 {port_name} 错误次数过多，断开连接")
                            port.close()
                            del self.active_connections[port_name]
                
                await asyncio.sleep(0.1)  # 短暂休息
                
            except Exception as e:
                logger.error(f"传感器数据采集失败: {e}")
                await asyncio.sleep(1.0)
    
    async def process_sensor_line(self, port_name: str, raw_data: bytes):
        """处理单行传感器数据"""
        try:
            # 检测数据格式
            data_format = self.detect_data_format(raw_data)
            
            # 处理数据
            processed_data = self.data_processor.process_data(raw_data, data_format)
            
            if processed_data and processed_data.get('sensors'):
                # 发布到MQTT
                topic = f"sensors/{self.client_id}/{port_name}"
                mqtt_data = {
                    'type': 'sensor_data',
                    'port': port_name,
                    'data': processed_data,
                    'raw_data': raw_data.decode('utf-8', errors='ignore')
                }
                
                self.publish_data(topic, mqtt_data)
                
                # 更新连接信息
                self.active_connections[port_name]['last_data'] = datetime.now()
                
                logger.debug(f"处理端口 {port_name} 数据: {len(processed_data['sensors'])} 个传感器")
            
        except Exception as e:
            logger.error(f"传感器数据处理失败: {e}")
    
    def detect_data_format(self, raw_data: bytes) -> DataFormat:
        """检测数据格式"""
        try:
            data_str = raw_data.decode('utf-8', errors='ignore').strip()
            
            # 检测JSON
            if data_str.startswith('{') and data_str.endswith('}'):
                return DataFormat.JSON
            
            # 检测CSV
            if ',' in data_str and not data_str.startswith('{'):
                return DataFormat.CSV
            
            # 检测自定义格式
            if ':' in data_str and ';' in data_str:
                return DataFormat.CUSTOM
            
            # 检测二进制
            if len(raw_data) > 0 and raw_data[0] < 32:
                return DataFormat.BINARY
            
            # 默认CSV
            return DataFormat.CSV
            
        except Exception:
            return DataFormat.CSV
    
    async def capture_and_send_image(self):
        """捕获并发送图像"""
        try:
            logger.info("开始图像捕获...")
            
            if self.camera_enabled and self.camera_cap is not None:
                # 捕获真实图像
                ret, frame = self.camera_cap.read()
                if ret:
                    # 编码图像
                    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
                    result, encoded_img = cv2.imencode('.jpg', frame, encode_param)
                    
                    if result:
                        image_data = encoded_img.tobytes()
                        
                        # 处理图像数据
                        processed_data = {
                            'data': base64.b64encode(image_data).decode('utf-8'),
                            'format': 'jpg',
                            'size': len(image_data),
                            'hash': hashlib.md5(image_data).hexdigest(),
                            'encoding': 'base64',
                            'resolution': f"{frame.shape[1]}x{frame.shape[0]}"
                        }
                        
                        # 发布图像数据
                        topic = f"sensors/{self.client_id}/camera/image"
                        mqtt_data = {
                            'type': 'image',
                            'source': 'camera',
                            'data': processed_data
                        }
                        
                        self.publish_data(topic, mqtt_data)
                        logger.info("图像数据发布成功")
                        return
            
            # 生成模拟图像
            logger.info("生成模拟图像数据")
            fake_image = self.generate_fake_image()
            
            processed_data = {
                'data': base64.b64encode(fake_image).decode('utf-8'),
                'format': 'jpg',
                'size': len(fake_image),
                'hash': hashlib.md5(fake_image).hexdigest(),
                'encoding': 'base64',
                'resolution': '640x480'
            }
            
            # 发布模拟图像
            topic = f"sensors/{self.client_id}/camera/image"
            mqtt_data = {
                'type': 'image',
                'source': 'simulated',
                'data': processed_data
            }
            
            self.publish_data(topic, mqtt_data)
            
        except Exception as e:
            logger.error(f"图像捕获失败: {e}")
    
    def generate_fake_image(self) -> bytes:
        """生成模拟图像数据"""
        # 创建一个简单的彩色图像
        width, height = 640, 480
        image = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
        
        # 添加一些文本
        import time
        text = f"Simulated Image {int(time.time())}"
        
        # 编码为JPEG
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 80]
        result, encoded_img = cv2.imencode('.jpg', image, encode_param)
        
        if result:
            return encoded_img.tobytes()
        else:
            return b'fake_image_data'
    
    async def capture_sensor_snapshot(self):
        """捕获传感器快照"""
        try:
            logger.info("捕获传感器快照...")
            
            snapshot = {
                'timestamp': datetime.now().isoformat(),
                'active_connections': len(self.active_connections),
                'system_stats': self.get_system_stats(),
                'port_data': {}
            }
            
            # 获取每个端口的最新数据
            for port_name, connection in self.active_connections.items():
                port = connection['port']
                
                # 尝试读取当前数据
                raw_data = port.read(1024)
                if raw_data:
                    data_format = self.detect_data_format(raw_data)
                    processed_data = self.data_processor.process_data(raw_data, data_format)
                    
                    snapshot['port_data'][port_name] = {
                        'format': data_format.value,
                        'raw_data': raw_data.decode('utf-8', errors='ignore'),
                        'processed_data': processed_data
                    }
            
            # 发布快照
            topic = f"sensors/{self.client_id}/snapshot"
            mqtt_data = {
                'type': 'snapshot',
                'data': snapshot
            }
            
            self.publish_data(topic, mqtt_data)
            logger.info("传感器快照发布成功")
            
        except Exception as e:
            logger.error(f"传感器快照捕获失败: {e}")
    
    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        uptime = None
        if self.start_time:
            uptime = str(datetime.now() - self.start_time)
        
        return {
            'client_id': self.client_id,
            'running': self.running,
            'mqtt_connected': self.is_connected,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'uptime': uptime,
            'total_messages': self.total_messages,
            'error_count': self.error_count,
            'active_connections': len(self.active_connections),
            'camera_enabled': self.camera_enabled,
            'config': {
                'scan_interval': self.scan_interval,
                'image_interval': self.image_interval,
                'retry_interval': self.retry_interval
            }
        }
    
    async def periodic_tasks(self):
        """定期任务"""
        while self.running:
            try:
                # 定期扫描新端口
                await self.scan_and_connect_ports()
                
                # 定期捕获图像
                if self.camera_enabled:
                    await self.capture_and_send_image()
                
                # 发布状态信息
                stats = self.get_system_stats()
                self.publish_data(f"status/{self.client_id}", stats)
                
                await asyncio.sleep(self.scan_interval)
                
            except Exception as e:
                logger.error(f"定期任务失败: {e}")
                await asyncio.sleep(5.0)
    
    async def start(self):
        """启动客户端"""
        logger.info("启动增强的MQTT传感器客户端...")
        
        self.start_time = datetime.now()
        
        # 初始化摄像头
        if self.camera_enabled:
            try:
                self.camera_cap = cv2.VideoCapture(0)
                if not self.camera_cap.isOpened():
                    logger.warning("摄像头初始化失败，禁用摄像头功能")
                    self.camera_enabled = False
            except Exception as e:
                logger.warning(f"摄像头初始化失败: {e}")
                self.camera_enabled = False
        
        # 连接MQTT
        if not self.connect_mqtt():
            logger.error("MQTT连接失败")
            return
        
        # 等待MQTT连接
        await asyncio.sleep(2.0)
        
        # 启动设备管理器
        demo_devices = create_comprehensive_demo_setup(self.device_manager)
        self.device_manager.start_all_devices()
        
        # 初始扫描
        await self.scan_and_connect_ports()
        
        # 启动任务
        self.running = True
        
        tasks = [
            asyncio.create_task(self.collect_sensor_data()),
            asyncio.create_task(self.periodic_tasks())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            logger.info("接收到停止信号")
        finally:
            await self.stop()
    
    async def stop(self):
        """停止客户端"""
        logger.info("停止增强的MQTT传感器客户端...")
        
        self.running = False
        
        # 关闭串口连接
        for port_name, connection in self.active_connections.items():
            connection['port'].close()
        self.active_connections.clear()
        
        # 停止设备管理器
        self.device_manager.stop_all_devices()
        
        # 关闭摄像头
        if self.camera_cap:
            self.camera_cap.release()
        
        # 关闭MQTT
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
        
        logger.info("客户端已停止")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='增强的MQTT传感器客户端')
    parser.add_argument('--client-id', default=f'enhanced_sensor_{uuid.uuid4().hex[:8]}', help='客户端ID')
    parser.add_argument('--mqtt-host', default='localhost', help='MQTT服务器地址')
    parser.add_argument('--mqtt-port', type=int, default=1883, help='MQTT服务器端口')
    parser.add_argument('--scan-interval', type=float, default=30.0, help='端口扫描间隔')
    parser.add_argument('--image-interval', type=float, default=60.0, help='图像采集间隔')
    parser.add_argument('--camera', action='store_true', help='启用摄像头功能')
    
    args = parser.parse_args()
    
    # 配置MQTT
    mqtt_config = {
        'host': args.mqtt_host,
        'port': args.mqtt_port,
        'username': os.getenv('MQTT_USERNAME', ''),
        'password': os.getenv('MQTT_PASSWORD', ''),
        'keepalive': int(os.getenv('MQTT_KEEPALIVE', '60'))
    }
    
    # 创建客户端
    client = EnhancedMQTTSensorClient(args.client_id, mqtt_config)
    client.scan_interval = args.scan_interval
    client.image_interval = args.image_interval
    client.camera_enabled = args.camera
    
    # 启动客户端
    try:
        asyncio.run(client.start())
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.error(f"程序运行异常: {e}")


if __name__ == "__main__":
    main()
