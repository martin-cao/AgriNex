#!/usr/bin/env python3
"""
串口设备模拟器
模拟各种传感器设备通过串口发送数据
"""

import asyncio
import logging
import random
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
import json
import threading
import queue

# 虚拟串口库
try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False
    
# 使用内存队列模拟串口通信
import queue as Queue

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VirtualSerialPort:
    """虚拟串口类"""
    
    def __init__(self, port_name: str, baudrate: int = 9600):
        self.port_name = port_name
        self.baudrate = baudrate
        self.is_open = False
        self.read_queue = Queue.Queue()
        self.write_queue = Queue.Queue()
        self.timeout = 1.0
        
    def open(self):
        """打开串口"""
        self.is_open = True
        logger.info(f"虚拟串口 {self.port_name} 已打开")
        
    def close(self):
        """关闭串口"""
        self.is_open = False
        logger.info(f"虚拟串口 {self.port_name} 已关闭")
        
    def write(self, data: bytes):
        """写入数据"""
        if self.is_open:
            self.write_queue.put(data)
            
    def read(self, size: int = 1) -> bytes:
        """读取数据"""
        if not self.is_open:
            return b''
            
        try:
            data = self.read_queue.get(timeout=self.timeout)
            return data
        except Queue.Empty:
            return b''
    
    def readline(self) -> bytes:
        """读取一行数据"""
        if not self.is_open:
            return b''
            
        try:
            data = self.read_queue.get(timeout=self.timeout)
            return data
        except Queue.Empty:
            return b''
    
    def put_data(self, data: bytes):
        """向读取队列放入数据（模拟设备发送）"""
        if self.is_open:
            self.read_queue.put(data)


class BaseSensorDevice:
    """传感器设备基类"""
    
    def __init__(self, device_id: str, serial_port: VirtualSerialPort):
        self.device_id = device_id
        self.serial_port = serial_port
        self.running = False
        self.thread = None
        self.interval = 5.0  # 默认5秒发送一次数据
        
    def start(self):
        """启动设备"""
        self.running = True
        self.thread = threading.Thread(target=self._run)
        self.thread.daemon = True
        self.thread.start()
        logger.info(f"设备 {self.device_id} 已启动")
        
    def stop(self):
        """停止设备"""
        self.running = False
        if self.thread:
            self.thread.join()
        logger.info(f"设备 {self.device_id} 已停止")
        
    def _run(self):
        """运行循环"""
        while self.running:
            try:
                data = self.generate_data()
                if data:
                    self.serial_port.put_data(data)
                    logger.debug(f"设备 {self.device_id} 发送数据: {data}")
                    
                time.sleep(self.interval)
                
            except Exception as e:
                logger.error(f"设备 {self.device_id} 运行错误: {e}")
                time.sleep(1)
                
    def generate_data(self) -> bytes:
        """生成数据（子类实现）"""
        raise NotImplementedError
        
    def set_interval(self, interval: float):
        """设置数据发送间隔"""
        self.interval = interval


class EnvironmentSensorDevice(BaseSensorDevice):
    """环境传感器设备（温度、湿度、光照）"""
    
    def __init__(self, device_id: str, serial_port: VirtualSerialPort):
        super().__init__(device_id, serial_port)
        
        # 传感器参数
        self.temperature_range = (18.0, 32.0)
        self.humidity_range = (30.0, 85.0)
        self.light_range = (200.0, 2000.0)
        
        # 当前值（用于生成连续变化的数据）
        self.current_temperature = 25.0
        self.current_humidity = 60.0
        self.current_light = 1000.0
        
        # 变化幅度
        self.temp_change_rate = 0.5
        self.humidity_change_rate = 2.0
        self.light_change_rate = 50.0
        
    def generate_data(self) -> bytes:
        """生成环境传感器数据"""
        # 模拟数据的自然变化
        self.current_temperature += random.uniform(-self.temp_change_rate, self.temp_change_rate)
        self.current_humidity += random.uniform(-self.humidity_change_rate, self.humidity_change_rate)
        self.current_light += random.uniform(-self.light_change_rate, self.light_change_rate)
        
        # 限制在合理范围内
        self.current_temperature = max(self.temperature_range[0], 
                                     min(self.temperature_range[1], self.current_temperature))
        self.current_humidity = max(self.humidity_range[0], 
                                  min(self.humidity_range[1], self.current_humidity))
        self.current_light = max(self.light_range[0], 
                               min(self.light_range[1], self.current_light))
        
        # 生成串口数据格式: T:25.5,H:60.2,L:1200.0
        data = f"T:{self.current_temperature:.1f},H:{self.current_humidity:.1f},L:{self.current_light:.1f}\n"
        return data.encode('utf-8')


class TemperatureSensorDevice(BaseSensorDevice):
    """单纯的温度传感器"""
    
    def __init__(self, device_id: str, serial_port: VirtualSerialPort):
        super().__init__(device_id, serial_port)
        self.current_temperature = 25.0
        self.temp_range = (15.0, 35.0)
        
    def generate_data(self) -> bytes:
        """生成温度数据"""
        # 模拟温度变化
        change = random.uniform(-0.5, 0.5)
        self.current_temperature += change
        
        # 限制范围
        self.current_temperature = max(self.temp_range[0], 
                                     min(self.temp_range[1], self.current_temperature))
        
        # 只发送温度数据
        data = f"T:{self.current_temperature:.1f}\n"
        return data.encode('utf-8')


class HumiditySensorDevice(BaseSensorDevice):
    """湿度传感器"""
    
    def __init__(self, device_id: str, serial_port: VirtualSerialPort):
        super().__init__(device_id, serial_port)
        self.current_humidity = 60.0
        self.humidity_range = (20.0, 90.0)
        
    def generate_data(self) -> bytes:
        """生成湿度数据"""
        # 模拟湿度变化
        change = random.uniform(-2.0, 2.0)
        self.current_humidity += change
        
        # 限制范围
        self.current_humidity = max(self.humidity_range[0], 
                                  min(self.humidity_range[1], self.current_humidity))
        
        # 只发送湿度数据
        data = f"H:{self.current_humidity:.1f}\n"
        return data.encode('utf-8')


class LightSensorDevice(BaseSensorDevice):
    """光照传感器"""
    
    def __init__(self, device_id: str, serial_port: VirtualSerialPort):
        super().__init__(device_id, serial_port)
        self.current_light = 1000.0
        self.light_range = (0.0, 3000.0)
        
    def generate_data(self) -> bytes:
        """生成光照数据"""
        # 模拟光照变化（考虑时间因素）
        hour = datetime.now().hour
        
        # 白天光照强，夜晚光照弱
        if 6 <= hour <= 18:
            base_light = 800.0 + (hour - 6) * 100.0
        else:
            base_light = 100.0
            
        # 添加随机变化
        change = random.uniform(-50.0, 50.0)
        self.current_light = base_light + change
        
        # 限制范围
        self.current_light = max(self.light_range[0], 
                               min(self.light_range[1], self.current_light))
        
        # 只发送光照数据
        data = f"L:{self.current_light:.1f}\n"
        return data.encode('utf-8')


class SoilSensorDevice(BaseSensorDevice):
    """土壤传感器（湿度、pH值、EC值）"""
    
    def __init__(self, device_id: str, serial_port: VirtualSerialPort):
        super().__init__(device_id, serial_port)
        self.soil_moisture = 45.0
        self.soil_ph = 6.8
        self.soil_ec = 1.2
        
    def generate_data(self) -> bytes:
        """生成土壤数据"""
        # 模拟土壤参数变化
        self.soil_moisture += random.uniform(-1.0, 1.0)
        self.soil_ph += random.uniform(-0.1, 0.1)
        self.soil_ec += random.uniform(-0.05, 0.05)
        
        # 限制范围
        self.soil_moisture = max(0.0, min(100.0, self.soil_moisture))
        self.soil_ph = max(5.0, min(8.0, self.soil_ph))
        self.soil_ec = max(0.5, min(3.0, self.soil_ec))
        
        # 生成土壤数据格式: SM:45.2,PH:6.8,EC:1.2
        data = f"SM:{self.soil_moisture:.1f},PH:{self.soil_ph:.1f},EC:{self.soil_ec:.1f}\n"
        return data.encode('utf-8')


class WeatherStationDevice(BaseSensorDevice):
    """气象站设备（温度、湿度、气压、风速）"""
    
    def __init__(self, device_id: str, serial_port: VirtualSerialPort):
        super().__init__(device_id, serial_port)
        self.temperature = 25.0
        self.humidity = 60.0
        self.pressure = 1013.25
        self.wind_speed = 3.0
        
    def generate_data(self) -> bytes:
        """生成气象站数据"""
        # 模拟气象参数变化
        self.temperature += random.uniform(-0.5, 0.5)
        self.humidity += random.uniform(-2.0, 2.0)
        self.pressure += random.uniform(-1.0, 1.0)
        self.wind_speed += random.uniform(-0.5, 0.5)
        
        # 限制范围
        self.temperature = max(-10.0, min(50.0, self.temperature))
        self.humidity = max(0.0, min(100.0, self.humidity))
        self.pressure = max(950.0, min(1050.0, self.pressure))
        self.wind_speed = max(0.0, min(20.0, self.wind_speed))
        
        # 生成气象数据格式: T:25.0,H:60.0,P:1013.25,W:3.0
        data = f"T:{self.temperature:.1f},H:{self.humidity:.1f},P:{self.pressure:.2f},W:{self.wind_speed:.1f}\n"
        return data.encode('utf-8')


class SerialDeviceManager:
    """串口设备管理器"""
    
    def __init__(self):
        self.virtual_ports = {}
        self.devices = {}
        self.running = False
        
    def create_virtual_port(self, port_name: str, baudrate: int = 9600) -> VirtualSerialPort:
        """创建虚拟串口"""
        if port_name not in self.virtual_ports:
            self.virtual_ports[port_name] = VirtualSerialPort(port_name, baudrate)
            logger.info(f"创建虚拟串口: {port_name}")
        return self.virtual_ports[port_name]
    
    def add_device(self, device: BaseSensorDevice):
        """添加设备"""
        self.devices[device.device_id] = device
        logger.info(f"添加设备: {device.device_id}")
    
    def start_all_devices(self):
        """启动所有设备"""
        self.running = True
        for device in self.devices.values():
            device.start()
        logger.info("所有设备已启动")
    
    def stop_all_devices(self):
        """停止所有设备"""
        self.running = False
        for device in self.devices.values():
            device.stop()
        logger.info("所有设备已停止")
    
    def get_port(self, port_name: str) -> Optional[VirtualSerialPort]:
        """获取虚拟串口"""
        return self.virtual_ports.get(port_name)
    
    def list_ports(self) -> List[str]:
        """列出所有虚拟串口"""
        return list(self.virtual_ports.keys())
    
    def set_device_interval(self, device_id: str, interval: float):
        """设置设备数据发送间隔"""
        if device_id in self.devices:
            self.devices[device_id].set_interval(interval)
            logger.info(f"设备 {device_id} 间隔设置为 {interval}s")


def create_demo_devices(manager: SerialDeviceManager):
    """创建演示设备"""
    
    # 创建环境传感器
    env_port = manager.create_virtual_port("COM1", 9600)
    env_device = EnvironmentSensorDevice("ENV_001", env_port)
    manager.add_device(env_device)
    
    # 创建温度传感器
    temp_port = manager.create_virtual_port("COM2", 9600)
    temp_device = TemperatureSensorDevice("TEMP_001", temp_port)
    manager.add_device(temp_device)
    
    # 创建湿度传感器
    hum_port = manager.create_virtual_port("COM3", 9600)
    hum_device = HumiditySensorDevice("HUM_001", hum_port)
    manager.add_device(hum_device)
    
    # 创建光照传感器
    light_port = manager.create_virtual_port("COM4", 9600)
    light_device = LightSensorDevice("LIGHT_001", light_port)
    manager.add_device(light_device)
    
    # 创建土壤传感器
    soil_port = manager.create_virtual_port("COM5", 9600)
    soil_device = SoilSensorDevice("SOIL_001", soil_port)
    manager.add_device(soil_device)
    
    # 创建气象站
    weather_port = manager.create_virtual_port("COM6", 9600)
    weather_device = WeatherStationDevice("WEATHER_001", weather_port)
    manager.add_device(weather_device)
    
    logger.info("演示设备创建完成")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='串口设备模拟器')
    parser.add_argument('--interval', type=float, default=5.0, help='数据发送间隔(秒)')
    parser.add_argument('--devices', nargs='+', 
                       choices=['env', 'temp', 'hum', 'light', 'soil', 'weather', 'all'],
                       default=['all'], help='要启动的设备类型')
    
    args = parser.parse_args()
    
    # 创建设备管理器
    manager = SerialDeviceManager()
    
    # 创建演示设备
    create_demo_devices(manager)
    
    # 设置数据发送间隔
    for device_id in manager.devices:
        manager.set_device_interval(device_id, args.interval)
    
    try:
        # 启动所有设备
        manager.start_all_devices()
        
        logger.info("串口设备模拟器正在运行...")
        logger.info("可用的虚拟串口:")
        for port in manager.list_ports():
            logger.info(f"  - {port}")
        
        logger.info("按 Ctrl+C 停止模拟器")
        
        # 保持运行
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("接收到停止信号")
        
    finally:
        manager.stop_all_devices()
        logger.info("串口设备模拟器已停止")


if __name__ == "__main__":
    main()
