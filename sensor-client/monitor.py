#!/usr/bin/env python3
"""
AgriNex 传感器客户端状态监控
监控MQTT连接状态和传感器数据流
"""

import asyncio
import json
import logging
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Set

import paho.mqtt.client as mqtt

# 添加项目路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir.parent))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SensorClientMonitor:
    """传感器客户端监控器"""
    
    def __init__(self, mqtt_host: str = 'localhost', mqtt_port: int = 1883):
        self.mqtt_host = mqtt_host
        self.mqtt_port = mqtt_port
        self.client = None
        self.running = False
        
        # 监控数据
        self.active_clients: Set[str] = set()
        self.client_stats: Dict[str, Dict[str, Any]] = {}
        self.last_message_time: Dict[str, datetime] = {}
        
        # 统计信息
        self.total_messages = 0
        self.start_time = None
    
    def on_connect(self, client, userdata, flags, rc):
        """MQTT连接回调"""
        if rc == 0:
            logger.info("监控器连接到MQTT服务器成功")
            
            # 订阅所有传感器主题
            topics = [
                'sensors/+/+',           # 传感器数据
                'status/+',              # 状态信息
                'response/+/+',          # 响应消息
                'control/+/+',           # 控制消息
            ]
            
            for topic in topics:
                client.subscribe(topic)
                logger.info(f"订阅主题: {topic}")
        else:
            logger.error(f"连接失败: {rc}")
    
    def on_message(self, client, userdata, msg):
        """消息接收回调"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            
            self.total_messages += 1
            
            # 解析主题
            topic_parts = topic.split('/')
            
            if len(topic_parts) >= 2:
                topic_type = topic_parts[0]
                client_id = topic_parts[1]
                
                # 更新客户端活动时间
                self.last_message_time[client_id] = datetime.now()
                self.active_clients.add(client_id)
                
                # 处理不同类型的消息
                if topic_type == 'sensors':
                    self.handle_sensor_data(client_id, topic, payload)
                elif topic_type == 'status':
                    self.handle_status_data(client_id, topic, payload)
                elif topic_type == 'response':
                    self.handle_response_data(client_id, topic, payload)
                
                # 更新统计信息
                if client_id not in self.client_stats:
                    self.client_stats[client_id] = {
                        'message_count': 0,
                        'last_seen': None,
                        'sensor_count': 0,
                        'status': 'unknown'
                    }
                
                self.client_stats[client_id]['message_count'] += 1
                self.client_stats[client_id]['last_seen'] = datetime.now()
                
        except Exception as e:
            logger.error(f"消息处理失败: {e}")
    
    def handle_sensor_data(self, client_id: str, topic: str, payload: Dict[str, Any]):
        """处理传感器数据"""
        try:
            data_type = payload.get('type', 'unknown')
            port = payload.get('port', 'unknown')
            
            # 更新传感器计数
            if client_id in self.client_stats:
                sensor_data = payload.get('data', {})
                sensors = sensor_data.get('sensors', {})
                self.client_stats[client_id]['sensor_count'] = len(sensors)
            
            logger.debug(f"[{client_id}] 传感器数据: {data_type} from {port}")
            
        except Exception as e:
            logger.error(f"传感器数据处理失败: {e}")
    
    def handle_status_data(self, client_id: str, topic: str, payload: Dict[str, Any]):
        """处理状态数据"""
        try:
            if client_id in self.client_stats:
                self.client_stats[client_id]['status'] = payload.get('mqtt_connected', False)
                
                # 更新详细状态
                self.client_stats[client_id].update({
                    'running': payload.get('running', False),
                    'mqtt_connected': payload.get('mqtt_connected', False),
                    'uptime': payload.get('uptime', 'unknown'),
                    'active_connections': payload.get('active_connections', 0),
                    'camera_enabled': payload.get('camera_enabled', False)
                })
            
            logger.debug(f"[{client_id}] 状态更新: {payload.get('mqtt_connected', False)}")
            
        except Exception as e:
            logger.error(f"状态数据处理失败: {e}")
    
    def handle_response_data(self, client_id: str, topic: str, payload: Dict[str, Any]):
        """处理响应数据"""
        try:
            command = topic.split('/')[-1]
            status = payload.get('status', 'unknown')
            
            logger.info(f"[{client_id}] 响应 {command}: {status}")
            
        except Exception as e:
            logger.error(f"响应数据处理失败: {e}")
    
    def print_status(self):
        """打印状态信息"""
        os.system('clear' if os.name == 'posix' else 'cls')
        
        print("=" * 80)
        print("AgriNex 传感器客户端监控器")
        print("=" * 80)
        
        # 系统信息
        uptime = datetime.now() - self.start_time if self.start_time else None
        print(f"运行时间: {uptime}")
        print(f"总消息数: {self.total_messages}")
        print(f"活跃客户端: {len(self.active_clients)}")
        print()
        
        # 客户端状态
        if self.client_stats:
            print("客户端状态:")
            print("-" * 80)
            print(f"{'客户端ID':<20} {'状态':<10} {'消息数':<8} {'传感器':<8} {'最后活动':<20}")
            print("-" * 80)
            
            for client_id, stats in self.client_stats.items():
                status = "在线" if stats.get('mqtt_connected', False) else "离线"
                last_seen = stats.get('last_seen')
                last_seen_str = last_seen.strftime('%H:%M:%S') if last_seen else '未知'
                
                print(f"{client_id:<20} {status:<10} {stats['message_count']:<8} "
                      f"{stats.get('sensor_count', 0):<8} {last_seen_str:<20}")
        else:
            print("暂无客户端连接")
        
        print("\n按 Ctrl+C 停止监控")
    
    def connect_mqtt(self) -> bool:
        """连接MQTT服务器"""
        try:
            self.client = mqtt.Client(client_id="sensor_monitor")
            self.client.on_connect = self.on_connect
            self.client.on_message = self.on_message
            
            self.client.connect(self.mqtt_host, self.mqtt_port, 60)
            self.client.loop_start()
            
            return True
            
        except Exception as e:
            logger.error(f"MQTT连接失败: {e}")
            return False
    
    async def monitor_loop(self):
        """监控循环"""
        while self.running:
            try:
                self.print_status()
                await asyncio.sleep(5)  # 每5秒更新一次显示
                
            except Exception as e:
                logger.error(f"监控循环失败: {e}")
                await asyncio.sleep(1)
    
    def setup_signal_handlers(self):
        """设置信号处理器"""
        def signal_handler(signum, frame):
            logger.info("接收到停止信号")
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def start(self):
        """启动监控器"""
        logger.info("启动传感器客户端监控器...")
        
        self.start_time = datetime.now()
        
        # 连接MQTT
        if not self.connect_mqtt():
            logger.error("无法连接到MQTT服务器")
            return
        
        # 等待连接建立
        await asyncio.sleep(2)
        
        # 设置信号处理器
        self.setup_signal_handlers()
        
        # 开始监控
        self.running = True
        
        try:
            await self.monitor_loop()
        except KeyboardInterrupt:
            logger.info("用户中断监控")
        finally:
            await self.stop()
    
    async def stop(self):
        """停止监控器"""
        logger.info("停止监控器...")
        
        self.running = False
        
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
        
        logger.info("监控器已停止")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AgriNex 传感器客户端监控器')
    parser.add_argument('--mqtt-host', default='localhost', help='MQTT服务器地址')
    parser.add_argument('--mqtt-port', type=int, default=1883, help='MQTT服务器端口')
    
    args = parser.parse_args()
    
    # 创建监控器
    monitor = SensorClientMonitor(args.mqtt_host, args.mqtt_port)
    
    # 启动监控
    try:
        asyncio.run(monitor.start())
    except KeyboardInterrupt:
        logger.info("监控器被用户中断")
    except Exception as e:
        logger.error(f"监控器运行异常: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    import os
    sys.exit(main())
