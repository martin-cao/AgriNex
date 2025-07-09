#!/usr/bin/env python3
"""
快速MQTT诊断脚本
"""
import os
import sys
import subprocess
import socket
import time

def check_mqtt_port():
    """检查MQTT端口是否开放"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 1883))
        sock.close()
        return result == 0
    except:
        return False

def check_mqtt_process():
    """检查mosquitto进程"""
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        return 'mosquitto' in result.stdout
    except:
        return False

def test_mqtt_client():
    """测试MQTT客户端连接"""
    try:
        import paho.mqtt.client as mqtt
        
        connected = False
        def on_connect(client, userdata, flags, rc):
            nonlocal connected
            connected = (rc == 0)
        
        client = mqtt.Client()
        client.on_connect = on_connect
        client.connect('localhost', 1883, 60)
        client.loop_start()
        time.sleep(2)
        client.loop_stop()
        client.disconnect()
        
        return connected
    except Exception as e:
        print(f"MQTT客户端测试错误: {e}")
        return False

def main():
    print("=== MQTT快速诊断 ===")
    print(f"1. 检查MQTT端口1883: {'✓' if check_mqtt_port() else '✗'}")
    print(f"2. 检查mosquitto进程: {'✓' if check_mqtt_process() else '✗'}")
    print(f"3. 测试MQTT客户端: {'✓' if test_mqtt_client() else '✗'}")
    
    if all([check_mqtt_port(), check_mqtt_process(), test_mqtt_client()]):
        print("\n🎉 MQTT服务正常运行!")
        
        # 显示mosquitto进程信息
        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            lines = result.stdout.split('\n')
            for line in lines:
                if 'mosquitto' in line and 'grep' not in line:
                    print(f"进程信息: {line}")
        except:
            pass
            
        print("\n建议:")
        print("1. 确保后端应用中的MQTT_HOST配置为 'localhost'")
        print("2. 确保后端应用中的MQTT_PORT配置为 1883")
        print("3. 检查防火墙设置，确保1883端口可访问")
        
    else:
        print("\n❌ MQTT服务有问题，请检查:")
        print("1. mosquitto是否正在运行")
        print("2. 配置文件是否正确")
        print("3. 端口是否被占用")

if __name__ == "__main__":
    main()
