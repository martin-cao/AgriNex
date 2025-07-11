#!/usr/bin/env python3
"""
MQTT 传感器客户端 - 支持数值传感器和图像/视频数据
支持串口通信和网络传输
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
import serial
import serial.tools.list_ports
from pathlib import Path

import paho.mqtt.client as mqtt
from paho.mqtt.client import MQTTMessage
import cv2
import numpy as np


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


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
    
    def process_video_data(self, video_data: bytes, format_type: str = 'mp4') -> Dict[str, Any]:
        """处理视频数据"""
        try:
            # 计算文件哈希
            file_hash = hashlib.md5(video_data).hexdigest()
            
            # 编码为base64
            encoded_data = base64.b64encode(video_data).decode('utf-8')
            
            return {
                'data': encoded_data,
                'format': format_type,
                'size': len(video_data),
                'hash': file_hash,
                'encoding': 'base64'
            }
        except Exception as e:
            logger.error(f"视频数据处理失败: {e}")
            return {}


class SerialConnector:
    """串口连接器"""
    
    def __init__(self, port: Optional[str] = None, baudrate: int = 9600):
        self.port = port
        self.baudrate = baudrate
        self.connection = None
        self.is_connected = False
    
    def scan_ports(self) -> List[str]:
        """扫描可用串口"""
        ports = serial.tools.list_ports.comports()
        available_ports = []
        
        for port in ports:
            available_ports.append(port.device)
            logger.info(f"发现串口: {port.device} - {port.description}")
        
        return available_ports
    
    def connect(self, port: Optional[str] = None) -> bool:
        """连接串口"""
        try:
            if port:
                self.port = port
            
            if not self.port:
                # 自动选择第一个可用串口
                available_ports = self.scan_ports()
                if available_ports:
                    self.port = available_ports[0]
                else:
                    logger.error("未找到可用串口")
                    return False
            
            self.connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1.0
            )
            
            self.is_connected = True
            logger.info(f"串口连接成功: {self.port}")
            return True
            
        except Exception as e:
            logger.error(f"串口连接失败: {e}")
            return False
    
    def read_data(self, timeout: float = 5.0) -> Optional[bytes]:
        """读取串口数据"""
        if not self.is_connected or not self.connection:
            return None
        
        try:
            # 设置超时
            self.connection.timeout = timeout
            data = self.connection.readline()
            return data if data else None
            
        except Exception as e:
            logger.error(f"串口读取失败: {e}")
            return None
    
    def close(self):
        """关闭串口连接"""
        if self.connection:
            self.connection.close()
            self.is_connected = False
            logger.info("串口连接已关闭")


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


class MQTTSensorClient:
    """MQTT传感器客户端"""
    
    def __init__(self, client_id: str, mqtt_config: Dict[str, Any]):
        self.client_id = client_id
        self.mqtt_config = mqtt_config
        self.client = None
        self.is_connected = False
        self.processor = SensorDataProcessor()
        self.serial_connector = SerialConnector()
        self.camera_connector = CameraConnector()
        
        # 运行配置
        self.running = False
        self.numeric_interval = 10.0  # 数值数据采集间隔(秒)
        self.image_interval = 60.0    # 图像数据采集间隔(秒)
        
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
    
    def on_message(self, client, userdata, msg: MQTTMessage):
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
                processed_data = None
                
                if self.serial_connector.is_connected:
                    # 从串口读取数据
                    raw_data = self.serial_connector.read_data()
                    if raw_data:
                        data_str = raw_data.decode('utf-8').strip()
                        processed_data = self.processor.process_numeric_data(data_str)
                        logger.info(f"从串口读取数据: {data_str}")
                
                # 如果串口没有数据或者串口未连接，使用模拟数据
                if not processed_data:
                    import random
                    processed_data = {
                        'temperature': round(random.uniform(20.0, 30.0), 1),
                        'temperature_unit': '°C',
                        'humidity': round(random.uniform(40.0, 80.0), 1),
                        'humidity_unit': '%',
                        'light': round(random.uniform(800.0, 1500.0), 1),
                        'light_unit': 'lux'
                    }
                    logger.info(f"使用模拟数据: {processed_data}")
                
                if processed_data:
                    # 发布到MQTT
                    topic = f"sensors/{self.client_id}/numeric"
                    mqtt_data = {
                        'type': 'numeric',
                        'data': processed_data
                    }
                    self.publish_data(topic, mqtt_data)
                
                await asyncio.sleep(self.numeric_interval)
                
            except Exception as e:
                logger.error(f"数值数据采集失败: {e}")
                await asyncio.sleep(5.0)
    
    async def capture_and_send_image(self):
        """捕获并发送图像数据"""
        try:
            if not self.camera_connector.is_connected:
                logger.warning("摄像头未连接，跳过图像捕获")
                return
            
            # 捕获图像
            image_data = self.camera_connector.capture_image('jpg')
            if image_data:
                processed_data = self.processor.process_image_data(image_data, 'jpg')
                
                if processed_data:
                    # 发布到MQTT
                    topic = f"sensors/{self.client_id}/image"
                    mqtt_data = {
                        'type': 'image',
                        'data': processed_data
                    }
                    self.publish_data(topic, mqtt_data)
                    
        except Exception as e:
            logger.error(f"图像数据捕获失败: {e}")
    
    async def capture_and_send_video(self):
        """捕获并发送视频数据"""
        try:
            # 这里可以实现视频录制逻辑
            # 由于视频文件较大，建议使用分片上传或直接流式传输
            logger.info("视频捕获功能待实现")
            
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
    
    async def start(self):
        """启动传感器客户端"""
        logger.info("启动传感器客户端...")
        
        # 连接MQTT
        if not self.connect_mqtt():
            logger.error("MQTT连接失败")
            return
        
        # 等待MQTT连接
        await asyncio.sleep(2.0)
        
        # 连接串口（可选）
        if not self.serial_connector.connect():
            logger.warning("串口连接失败，将使用模拟数据")
        
        # 连接摄像头（可选）
        if not self.camera_connector.connect():
            logger.warning("摄像头连接失败，将跳过图像采集")
        
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
        self.camera_connector.close()
        
        logger.info("传感器客户端已停止")


def main():
    """主函数"""
    # 配置
    client_id = os.getenv('SENSOR_CLIENT_ID', f'sensor_{uuid.uuid4().hex[:8]}')
    
    mqtt_config = {
        'host': os.getenv('MQTT_HOST', 'localhost'),
        'port': int(os.getenv('MQTT_PORT', '1883')),
        'username': os.getenv('MQTT_USERNAME', ''),
        'password': os.getenv('MQTT_PASSWORD', ''),
        'keepalive': int(os.getenv('MQTT_KEEPALIVE', '60'))
    }
    
    # 创建客户端
    client = MQTTSensorClient(client_id, mqtt_config)
    
    # 启动客户端
    try:
        asyncio.run(client.start())
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.error(f"程序运行异常: {e}")


if __name__ == "__main__":
    main()
