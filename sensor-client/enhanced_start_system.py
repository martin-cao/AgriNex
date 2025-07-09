#!/usr/bin/env python3
"""
一键启动脚本 - 增强的MQTT传感器系统
"""

import os
import sys
import subprocess
import time
import logging
import argparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_dependencies():
    """检查依赖项"""
    logger.info("检查依赖项...")
    
    missing_deps = []
    
    # 检查Python模块
    try:
        import paho.mqtt.client as mqtt
        logger.info("✓ paho-mqtt 已安装")
    except ImportError:
        missing_deps.append("paho-mqtt")
        logger.warning("✗ paho-mqtt 未安装")
    
    try:
        import numpy
        logger.info("✓ numpy 已安装")
    except ImportError:
        missing_deps.append("numpy")
        logger.warning("✗ numpy 未安装")
    
    try:
        import cv2
        logger.info("✓ opencv-python 已安装")
    except ImportError:
        logger.warning("✗ opencv-python 未安装 (图像功能将受限)")
    
    try:
        import serial
        logger.info("✓ pyserial 已安装")
    except ImportError:
        logger.warning("✗ pyserial 未安装 (将使用虚拟串口)")
    
    # 检查mosquitto
    try:
        result = subprocess.run(['mosquitto', '--help'], capture_output=True, timeout=5)
        if result.returncode == 0:
            logger.info("✓ mosquitto 已安装")
        else:
            missing_deps.append("mosquitto")
            logger.warning("✗ mosquitto 未安装")
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        missing_deps.append("mosquitto")
        logger.warning("✗ mosquitto 未安装")
    
    return missing_deps


def install_dependencies():
    """安装依赖项"""
    logger.info("尝试安装Python依赖项...")
    
    python_deps = ["paho-mqtt", "numpy", "opencv-python", "pyserial"]
    
    for dep in python_deps:
        try:
            logger.info(f"安装 {dep}...")
            subprocess.run([sys.executable, "-m", "pip", "install", dep], 
                         check=True, capture_output=True)
            logger.info(f"✓ {dep} 安装成功")
        except subprocess.CalledProcessError as e:
            logger.error(f"✗ {dep} 安装失败: {e}")


def show_help():
    """显示帮助信息"""
    help_text = """
增强的MQTT传感器系统 - 使用指南

系统组件:
1. enhanced_serial_simulator.py - 增强的串口设备模拟器
2. enhanced_mqtt_client.py - 增强的MQTT客户端
3. enhanced_simple_demo.py - 简化演示脚本
4. enhanced_system_test.py - 系统测试脚本

使用方法:

1. 快速演示 (不需要MQTT代理):
   python enhanced_simple_demo.py --duration 60

2. 完整MQTT系统演示:
   # 终端1: 启动MQTT代理
   mosquitto -p 1883 -v
   
   # 终端2: 启动MQTT客户端
   python enhanced_mqtt_client.py --client-id demo_client

3. 系统测试:
   python enhanced_system_test.py --duration 300 --clients 3

4. 只运行串口模拟器:
   python enhanced_serial_simulator.py --interval 5.0

依赖项安装:
- Python包: pip install paho-mqtt numpy opencv-python pyserial
- MQTT代理: 
  - macOS: brew install mosquitto
  - Ubuntu: sudo apt-get install mosquitto
  - Windows: 下载mosquitto安装包

文件说明:
- enhanced_serial_simulator.py: 支持多种传感器设备和数据格式的虚拟串口模拟器
- enhanced_mqtt_client.py: 支持多格式数据处理的MQTT客户端
- enhanced_simple_demo.py: 不需要MQTT代理的简化演示
- enhanced_system_test.py: 完整的系统集成测试
"""
    print(help_text)


def run_simple_demo(duration=60):
    """运行简化演示"""
    logger.info("启动简化演示...")
    
    try:
        cmd = [sys.executable, "enhanced_simple_demo.py", "--duration", str(duration)]
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"简化演示失败: {e}")
    except KeyboardInterrupt:
        logger.info("演示被用户中断")


def start_mqtt_broker():
    """启动MQTT代理"""
    logger.info("启动MQTT代理...")
    
    try:
        # 尝试启动mosquitto
        process = subprocess.Popen(
            ['mosquitto', '-p', '1883', '-v'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # 等待启动
        time.sleep(2)
        
        if process.poll() is None:
            logger.info("MQTT代理启动成功 (PID: %d)", process.pid)
            return process
        else:
            logger.error("MQTT代理启动失败")
            return None
            
    except FileNotFoundError:
        logger.error("mosquitto未找到，请先安装mosquitto")
        return None
    except Exception as e:
        logger.error(f"启动MQTT代理失败: {e}")
        return None


def run_full_demo(duration=120):
    """运行完整演示"""
    logger.info("启动完整MQTT系统演示...")
    
    # 启动MQTT代理
    mqtt_process = start_mqtt_broker()
    if not mqtt_process:
        logger.error("无法启动MQTT代理，退出")
        return
    
    client_process = None
    
    try:
        # 等待MQTT代理稳定
        time.sleep(3)
        
        # 启动MQTT客户端
        logger.info("启动MQTT客户端...")
        client_cmd = [
            sys.executable, "enhanced_mqtt_client.py",
            "--client-id", "demo_client",
            "--mqtt-host", "localhost",
            "--mqtt-port", "1883",
            "--scan-interval", "10.0"
        ]
        
        client_process = subprocess.Popen(client_cmd)
        
        # 等待指定时间
        logger.info(f"系统运行中，持续时间: {duration}s")
        logger.info("按 Ctrl+C 停止演示")
        
        time.sleep(duration)
        
    except KeyboardInterrupt:
        logger.info("演示被用户中断")
    except Exception as e:
        logger.error(f"完整演示失败: {e}")
    finally:
        # 清理进程
        try:
            if client_process:
                client_process.terminate()
                client_process.wait()
        except:
            pass
        
        try:
            if mqtt_process:
                mqtt_process.terminate()
                mqtt_process.wait()
        except:
            pass
        
        logger.info("演示结束")


def run_system_test(duration=300, clients=3):
    """运行系统测试"""
    logger.info("启动系统测试...")
    
    try:
        cmd = [
            sys.executable, "enhanced_system_test.py",
            "--duration", str(duration),
            "--clients", str(clients)
        ]
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"系统测试失败: {e}")
    except KeyboardInterrupt:
        logger.info("测试被用户中断")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='增强的MQTT传感器系统一键启动脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('command', nargs='?', default='help',
                       choices=['help', 'check', 'install', 'demo', 'full', 'test'],
                       help='执行的命令')
    parser.add_argument('--duration', type=int, default=60,
                       help='演示或测试持续时间(秒)')
    parser.add_argument('--clients', type=int, default=3,
                       help='测试客户端数量')
    
    args = parser.parse_args()
    
    if args.command == 'help':
        show_help()
        
    elif args.command == 'check':
        logger.info("检查系统依赖项...")
        missing_deps = check_dependencies()
        
        if missing_deps:
            logger.warning(f"缺少依赖项: {', '.join(missing_deps)}")
            logger.info("运行 'python enhanced_start_system.py install' 尝试自动安装")
        else:
            logger.info("所有依赖项都已安装 ✓")
            
    elif args.command == 'install':
        install_dependencies()
        logger.info("依赖项安装完成，请运行 'check' 命令验证")
        
    elif args.command == 'demo':
        logger.info("启动简化演示 (不需要MQTT代理)")
        run_simple_demo(args.duration)
        
    elif args.command == 'full':
        logger.info("启动完整MQTT系统演示")
        run_full_demo(args.duration)
        
    elif args.command == 'test':
        logger.info("启动系统测试")
        run_system_test(args.duration, args.clients)
        
    else:
        show_help()


if __name__ == "__main__":
    main()
