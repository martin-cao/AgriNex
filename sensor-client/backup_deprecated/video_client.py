#!/usr/bin/env python3
"""
视频捕获客户端示例
演示如何通过MQTT发送视频数据
"""

import asyncio
import json
import logging
import os
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
import base64
import hashlib

import paho.mqtt.client as mqtt
import cv2
import numpy as np


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VideoMQTTClient:
    """视频MQTT客户端"""
    
    def __init__(self, client_id: str, mqtt_config: Dict[str, Any]):
        self.client_id = client_id
        self.mqtt_config = mqtt_config
        self.client = None
        self.is_connected = False
        self.cap = None
        self.recording = False
        self.video_writer = None
        
        # 视频配置
        self.video_config = {
            'width': 640,
            'height': 480,
            'fps': 20,
            'format': 'mp4',
            'codec': 'XVID',
            'duration': 5  # 录制时长(秒)
        }
    
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
            if topic.endswith('/capture'):
                self.handle_capture_command(payload)
                
        except Exception as e:
            logger.error(f"消息处理失败: {e}")
    
    def handle_capture_command(self, payload: Dict[str, Any]):
        """处理捕获命令"""
        try:
            capture_type = payload.get('type', 'image')
            
            if capture_type == 'video':
                asyncio.create_task(self.record_and_send_video())
            elif capture_type == 'image':
                asyncio.create_task(self.capture_and_send_image())
                
        except Exception as e:
            logger.error(f"捕获命令处理失败: {e}")
    
    def init_camera(self) -> bool:
        """初始化摄像头"""
        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                logger.error("摄像头打开失败")
                return False
            
            # 设置摄像头参数
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.video_config['width'])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.video_config['height'])
            self.cap.set(cv2.CAP_PROP_FPS, self.video_config['fps'])
            
            logger.info("摄像头初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"摄像头初始化失败: {e}")
            return False
    
    def close_camera(self):
        """关闭摄像头"""
        if self.cap:
            self.cap.release()
            self.cap = None
            logger.info("摄像头已关闭")
    
    async def capture_and_send_image(self):
        """捕获并发送图像"""
        try:
            if not self.cap:
                logger.warning("摄像头未初始化")
                return
            
            ret, frame = self.cap.read()
            if not ret:
                logger.error("图像捕获失败")
                return
            
            # 编码图像
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
            result, encoded_img = cv2.imencode('.jpg', frame, encode_param)
            
            if not result:
                logger.error("图像编码失败")
                return
            
            # 转换为bytes
            image_bytes = encoded_img.tobytes()
            
            # 处理图像数据
            image_data = {
                'data': base64.b64encode(image_bytes).decode('utf-8'),
                'format': 'jpg',
                'size': len(image_bytes),
                'hash': hashlib.md5(image_bytes).hexdigest(),
                'encoding': 'base64'
            }
            
            # 发布到MQTT
            topic = f"sensors/{self.client_id}/image"
            mqtt_data = {
                'type': 'image',
                'data': image_data,
                'timestamp': datetime.utcnow().isoformat(),
                'client_id': self.client_id
            }
            
            self.publish_data(topic, mqtt_data)
            logger.info("图像数据发送成功")
            
        except Exception as e:
            logger.error(f"图像捕获和发送失败: {e}")
    
    async def record_and_send_video(self):
        """录制并发送视频"""
        try:
            if not self.cap:
                logger.warning("摄像头未初始化")
                return
            
            # 创建临时视频文件
            temp_filename = f"temp_video_{int(time.time())}.avi"
            
            # 初始化视频写入器
            fourcc = cv2.VideoWriter_fourcc(*self.video_config['codec'])
            self.video_writer = cv2.VideoWriter(
                temp_filename,
                fourcc,
                self.video_config['fps'],
                (self.video_config['width'], self.video_config['height'])
            )
            
            logger.info(f"开始录制视频: {temp_filename}")
            
            # 录制视频
            start_time = time.time()
            frame_count = 0
            
            while time.time() - start_time < self.video_config['duration']:
                ret, frame = self.cap.read()
                if not ret:
                    logger.error("视频帧读取失败")
                    break
                
                # 调整帧大小
                frame = cv2.resize(frame, (self.video_config['width'], self.video_config['height']))
                
                # 写入视频文件
                self.video_writer.write(frame)
                frame_count += 1
                
                # 控制帧率
                await asyncio.sleep(1.0 / self.video_config['fps'])
            
            # 关闭视频写入器
            self.video_writer.release()
            self.video_writer = None
            
            logger.info(f"视频录制完成，总帧数: {frame_count}")
            
            # 读取视频文件
            with open(temp_filename, 'rb') as f:
                video_bytes = f.read()
            
            # 删除临时文件
            try:
                os.remove(temp_filename)
            except:
                pass
            
            # 处理视频数据
            video_data = {
                'data': base64.b64encode(video_bytes).decode('utf-8'),
                'format': 'avi',
                'size': len(video_bytes),
                'hash': hashlib.md5(video_bytes).hexdigest(),
                'encoding': 'base64',
                'duration': self.video_config['duration'],
                'fps': self.video_config['fps'],
                'resolution': f"{self.video_config['width']}x{self.video_config['height']}"
            }
            
            # 发布到MQTT
            topic = f"sensors/{self.client_id}/video"
            mqtt_data = {
                'type': 'video',
                'data': video_data,
                'timestamp': datetime.utcnow().isoformat(),
                'client_id': self.client_id
            }
            
            self.publish_data(topic, mqtt_data)
            logger.info("视频数据发送成功")
            
        except Exception as e:
            logger.error(f"视频录制和发送失败: {e}")
            
            # 清理资源
            if self.video_writer:
                self.video_writer.release()
                self.video_writer = None
            
            try:
                if 'temp_filename' in locals():
                    os.remove(temp_filename)
            except:
                pass
    
    def publish_data(self, topic: str, data: Dict[str, Any], qos: int = 1) -> bool:
        """发布数据到MQTT"""
        if not self.is_connected or not self.client:
            logger.error("MQTT未连接")
            return False
        
        try:
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
    
    async def start_interactive_mode(self):
        """启动交互模式"""
        logger.info("进入交互模式")
        logger.info("可用命令:")
        logger.info("  i - 捕获图像")
        logger.info("  v - 录制视频")
        logger.info("  q - 退出")
        
        while True:
            try:
                command = input("请输入命令: ").strip().lower()
                
                if command == 'i':
                    await self.capture_and_send_image()
                elif command == 'v':
                    await self.record_and_send_video()
                elif command == 'q':
                    break
                else:
                    logger.info("无效命令，请重新输入")
                    
            except KeyboardInterrupt:
                break
            except EOFError:
                break
            except Exception as e:
                logger.error(f"命令处理异常: {e}")
    
    async def start(self):
        """启动客户端"""
        logger.info("启动视频MQTT客户端...")
        
        # 连接MQTT
        if not self.connect_mqtt():
            logger.error("MQTT连接失败")
            return
        
        # 等待MQTT连接
        await asyncio.sleep(2.0)
        
        # 初始化摄像头
        if not self.init_camera():
            logger.error("摄像头初始化失败")
            return
        
        # 启动交互模式
        await self.start_interactive_mode()
        
        # 清理资源
        self.close_camera()
        
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
        
        logger.info("客户端已停止")


def main():
    """主函数"""
    # 配置
    client_id = os.getenv('VIDEO_CLIENT_ID', f'video_{uuid.uuid4().hex[:8]}')
    
    mqtt_config = {
        'host': os.getenv('MQTT_HOST', 'localhost'),
        'port': int(os.getenv('MQTT_PORT', '1883')),
        'username': os.getenv('MQTT_USERNAME', ''),
        'password': os.getenv('MQTT_PASSWORD', ''),
        'keepalive': int(os.getenv('MQTT_KEEPALIVE', '60'))
    }
    
    # 创建客户端
    client = VideoMQTTClient(client_id, mqtt_config)
    
    # 启动客户端
    try:
        asyncio.run(client.start())
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.error(f"程序运行异常: {e}")


if __name__ == "__main__":
    main()
