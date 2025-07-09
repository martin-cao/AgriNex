#!/usr/bin/env python3
"""
诊断MQTT和后端连接
"""

import time
import json
import requests
import logging
from datetime import datetime
import paho.mqtt.client as mqtt

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def diagnose_system():
    """诊断系统状态"""
    
    print("🔍 系统诊断开始...")
    print("=" * 50)
    
    # 1. 检查MQTT代理
    print("\n1. 检查MQTT代理...")
    try:
        client = mqtt.Client()
        result = client.connect('localhost', 1883, 5)
        if result == 0:
            print("  ✅ MQTT代理正在运行")
            client.disconnect()
        else:
            print(f"  ❌ MQTT代理连接失败: {result}")
    except Exception as e:
        print(f"  ❌ MQTT代理连接错误: {e}")
    
    # 2. 检查后端服务
    print("\n2. 检查后端服务...")
    try:
        response = requests.get("http://localhost:5000/api/health", timeout=5)
        if response.status_code == 200:
            print("  ✅ 后端服务正在运行")
        else:
            print(f"  ❌ 后端服务异常: {response.status_code}")
    except Exception as e:
        print(f"  ❌ 后端服务连接错误: {e}")
    
    # 3. 发送测试数据
    print("\n3. 发送测试数据...")
    try:
        client = mqtt.Client()
        client.connect('localhost', 1883, 60)
        
        # 发送测试数据
        test_data = {
            'device_id': 'DIAG_DEVICE',
            'sensor_id': 'temp_01',
            'sensor_type': 'temperature',
            'value': 25.0,
            'unit': '°C',
            'timestamp': datetime.now().isoformat()
        }
        
        # 发送到后端期望的主题
        topic = "sensors/DIAG_DEVICE/numeric"
        payload = json.dumps(test_data)
        
        result = client.publish(topic, payload, qos=1)
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print("  ✅ 测试数据发送成功")
        else:
            print(f"  ❌ 测试数据发送失败: {result.rc}")
        
        client.disconnect()
        
    except Exception as e:
        print(f"  ❌ 测试数据发送错误: {e}")
    
    # 4. 检查数据库连接
    print("\n4. 检查数据库...")
    try:
        # 尝试通过API检查数据
        response = requests.get("http://localhost:5000/api/devices", timeout=5)
        if response.status_code == 200:
            print("  ✅ 数据库连接正常")
        else:
            print(f"  ❌ 数据库连接异常: {response.status_code}")
    except Exception as e:
        print(f"  ❌ 数据库连接错误: {e}")
    
    print("\n=" * 50)
    print("🎯 诊断完成")

if __name__ == "__main__":
    diagnose_system()
