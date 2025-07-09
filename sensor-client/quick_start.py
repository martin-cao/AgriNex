#!/usr/bin/env python3
"""
AgriNex 传感器客户端 - 快速启动脚本
简化版本，适用于快速测试和演示
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from pathlib import Path

# 添加项目路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir.parent))
sys.path.insert(0, str(current_dir))

# 配置简单日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def quick_start():
    """快速启动传感器客户端"""
    try:
        from enhanced_mqtt_client import EnhancedMQTTSensorClient
        
        # 简单配置
        client_id = f"quick_sensor_{datetime.now().strftime('%H%M%S')}"
        mqtt_config = {
            'host': 'localhost',
            'port': 1883,
            'username': '',
            'password': '',
            'keepalive': 60
        }
        
        logger.info("🚀 快速启动传感器客户端...")
        logger.info(f"客户端ID: {client_id}")
        logger.info(f"MQTT服务器: {mqtt_config['host']}:{mqtt_config['port']}")
        
        # 创建客户端
        client = EnhancedMQTTSensorClient(client_id, mqtt_config)
        
        # 基本配置
        client.scan_interval = 10.0  # 更快的扫描间隔
        client.image_interval = 30.0  # 更快的图像间隔
        client.camera_enabled = False  # 默认禁用摄像头
        
        # 启动客户端
        asyncio.run(client.start())
        
    except KeyboardInterrupt:
        logger.info("用户中断，程序退出")
    except Exception as e:
        logger.error(f"启动失败: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(quick_start())
