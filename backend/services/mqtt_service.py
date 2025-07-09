# backend/services/mqtt_service.py
import json
import logging
import time
from typing import Dict, Any, Optional, Callable

import paho.mqtt.client as mqtt
from flask import current_app

from backend.services.ingestion_service import IngestionService

logger = logging.getLogger(__name__)


class MQTTService:
    """MQTT服务 - 处理MQTT连接、订阅和消息分发"""
    
    def __init__(self, app=None):
        self.app = app
        self.client = None
        self.is_connected = False
        self.ingestion_service = IngestionService()
        self.message_handlers = {}
        self.connection_thread = None
        self.running = False
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化Flask应用"""
        self.app = app
        
        # 从配置获取MQTT参数
        self.mqtt_config = {
            'host': app.config.get('MQTT_HOST', 'localhost'),
            'port': app.config.get('MQTT_PORT', 1883),
            'username': app.config.get('MQTT_USERNAME', ''),
            'password': app.config.get('MQTT_PASSWORD', ''),
            'keepalive': app.config.get('MQTT_KEEPALIVE', 60)
        }
        
        # 注册应用关闭时的清理函数
        app.teardown_appcontext(self._teardown)
    
    def _teardown(self, exception):
        """应用关闭时的清理"""
        # 只在应用真正关闭时才断开连接，不在每次上下文销毁时断开
        # 这个方法现在不做任何事情，让MQTT保持连接
        pass
    
    def connect(self) -> bool:
        """连接到MQTT代理"""
        try:
            # 如果已经连接，先断开
            if self.client and self.is_connected:
                self.disconnect()
            
            # 创建MQTT客户端
            client_id = f"agrinex_backend_{int(time.time())}"
            self.client = mqtt.Client(client_id=client_id)
            
            # 设置回调函数
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message
            self.client.on_subscribe = self._on_subscribe
            self.client.on_unsubscribe = self._on_unsubscribe
            
            # 设置认证
            if self.mqtt_config['username'] and self.mqtt_config['password']:
                self.client.username_pw_set(
                    self.mqtt_config['username'],
                    self.mqtt_config['password']
                )
            
            # 连接到代理
            self.client.connect(
                self.mqtt_config['host'],
                self.mqtt_config['port'],
                self.mqtt_config['keepalive']
            )
            
            # 启动网络循环（保持连接）
            self.running = True
            self.client.loop_start()  # 使用loop_start而不是单独的线程
            
            logger.info("MQTT服务连接成功")
            return True
            
        except Exception as e:
            logger.error("MQTT连接失败: %s", e)
            return False
    
    def disconnect(self):
        """断开MQTT连接"""
        try:
            self.running = False
            
            if self.client:
                self.client.loop_stop()
                self.client.disconnect()
            
            logger.info("MQTT连接已断开")
            
        except Exception as e:
            logger.error("MQTT断开失败: %s", e)
    
    def _on_connect(self, client, userdata, flags, rc):
        """连接成功回调"""
        if rc == 0:
            self.is_connected = True
            logger.info("MQTT代理连接成功")
            
            # 订阅传感器数据主题
            self.subscribe_to_sensors()
            
        else:
            logger.error("MQTT连接失败，返回码: %s", rc)
    
    def _on_disconnect(self, client, userdata, rc):
        """断开连接回调"""
        self.is_connected = False
        if rc != 0:
            logger.warning("MQTT意外断开连接，返回码: %s", rc)
        else:
            logger.info("MQTT正常断开连接")
    
    def _on_message(self, client, userdata, msg):
        """消息接收回调"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode('utf-8'))
            
            logger.info("收到MQTT消息: %s", topic)
            
            # 处理传感器数据
            if topic.startswith('sensors/'):
                self._handle_sensor_data(topic, payload)
            
            # 调用自定义处理器
            if topic in self.message_handlers:
                self.message_handlers[topic](topic, payload)
                
        except Exception as e:
            logger.error("MQTT消息处理失败: %s", e)
    
    def _on_subscribe(self, client, userdata, mid, granted_qos):
        """订阅成功回调"""
        logger.info("MQTT订阅成功，消息ID: %s", mid)
    
    def _on_unsubscribe(self, client, userdata, mid):
        """取消订阅回调"""
        logger.info("MQTT取消订阅成功，消息ID: %s", mid)
    
    def _handle_sensor_data(self, topic: str, payload: Dict[str, Any]):
        """处理传感器数据"""
        try:
            # 使用应用上下文
            if self.app:
                with self.app.app_context():
                    reading = self.ingestion_service.ingest_mqtt_message(topic, payload)
                    if reading:
                        logger.info("传感器数据存储成功: ID=%s", reading.id)
                    else:
                        logger.warning("传感器数据存储失败")
            else:
                logger.error("应用上下文不可用")
                    
        except Exception as e:
            logger.error("传感器数据处理失败: %s", e)
    
    def subscribe_to_sensors(self):
        """订阅传感器数据主题"""
        if not self.is_connected:
            logger.warning("MQTT未连接，无法订阅")
            return False
        
        try:
            # 订阅所有传感器数据主题
            topics = [
                ("sensors/+/numeric", 1),    # 数值数据
                ("sensors/+/image", 1),      # 图像数据
                ("sensors/+/video", 1),      # 视频数据
            ]
            
            for topic, qos in topics:
                result = self.client.subscribe(topic, qos)
                if result[0] == mqtt.MQTT_ERR_SUCCESS:
                    logger.info("订阅成功: %s", topic)
                else:
                    logger.error("订阅失败: %s, 错误码: %s", topic, result[0])
            
            return True
            
        except Exception as e:
            logger.error("订阅传感器主题失败: %s", e)
            return False
    
    def publish(self, topic: str, payload: Dict[str, Any], qos: int = 1) -> bool:
        """发布消息到MQTT"""
        if not self.is_connected:
            logger.warning("MQTT未连接，无法发布消息")
            return False
        
        try:
            message = json.dumps(payload, ensure_ascii=False)
            result = self.client.publish(topic, message, qos=qos)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info("消息发布成功: %s", topic)
                return True
            else:
                logger.error("消息发布失败: %s, 错误码: %s", topic, result.rc)
                return False
                
        except Exception as e:
            logger.error("消息发布异常: %s", e)
            return False
    
    def send_sensor_config(self, client_id: str, config: Dict[str, Any]) -> bool:
        """发送传感器配置"""
        topic = f"control/{client_id}/config"
        return self.publish(topic, config)
    
    def send_capture_command(self, client_id: str, capture_type: str = 'image') -> bool:
        """发送捕获命令"""
        topic = f"control/{client_id}/capture"
        payload = {
            'type': capture_type,
            'timestamp': time.time()
        }
        return self.publish(topic, payload)
    
    def register_message_handler(self, topic: str, handler: Callable[[str, Dict[str, Any]], None]):
        """注册自定义消息处理器"""
        self.message_handlers[topic] = handler
        
        # 如果已连接，立即订阅
        if self.is_connected:
            self.client.subscribe(topic, 1)
    
    def unregister_message_handler(self, topic: str):
        """取消注册消息处理器"""
        if topic in self.message_handlers:
            del self.message_handlers[topic]
            
            # 如果已连接，取消订阅
            if self.is_connected:
                self.client.unsubscribe(topic)
    
    def get_connection_status(self) -> Dict[str, Any]:
        """获取连接状态"""
        return {
            'connected': self.is_connected,
            'running': self.running,
            'config': self.mqtt_config
        }


# 全局MQTT服务实例
mqtt_service = MQTTService()
