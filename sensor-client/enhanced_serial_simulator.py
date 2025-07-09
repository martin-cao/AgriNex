#!/usr/bin/env python3
"""
增强的串口设备模拟器
支持pyserial和多种传感器设备类型
"""

import asyncio
import logging
import random
import time
import threading
import queue
import json
import struct
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

# 尝试导入pyserial
try:
    import serial
    import serial.tools.list_ports
    PYSERIAL_AVAILABLE = True
except ImportError:
    PYSERIAL_AVAILABLE = False
    print("警告: pyserial未安装，使用内存队列模拟串口")

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataFormat(Enum):
    """数据格式枚举"""
    JSON = "json"
    CSV = "csv"
    BINARY = "binary"
    CUSTOM = "custom"


class SensorType(Enum):
    """传感器类型枚举"""
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    LIGHT = "light"
    SOIL_MOISTURE = "soil_moisture"
    SOIL_PH = "soil_ph"
    SOIL_EC = "soil_ec"
    PRESSURE = "pressure"
    WIND_SPEED = "wind_speed"
    WIND_DIRECTION = "wind_direction"
    RAIN_LEVEL = "rain_level"
    UV_INDEX = "uv_index"
    CO2 = "co2"
    NOISE = "noise"
    MOTION = "motion"
    DOOR_STATUS = "door_status"
    WATER_LEVEL = "water_level"
    FLOW_RATE = "flow_rate"
    VALVE_STATUS = "valve_status"
    PUMP_STATUS = "pump_status"


@dataclass
class SensorReading:
    """传感器读数数据类"""
    sensor_id: str
    sensor_type: SensorType
    value: Union[float, int, bool, str]
    unit: str
    timestamp: datetime
    device_id: str
    quality: float = 1.0  # 数据质量 0-1
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['sensor_type'] = self.sensor_type.value
        return data


class EnhancedVirtualSerialPort:
    """增强的虚拟串口类"""
    
    def __init__(self, port_name: str, baudrate: int = 9600, timeout: float = 1.0):
        self.port_name = port_name
        self.baudrate = baudrate
        self.timeout = timeout
        self.is_open = False
        
        # 使用队列模拟串口缓冲区
        self.read_buffer = queue.Queue()
        self.write_buffer = queue.Queue()
        
        # 统计信息
        self.bytes_read = 0
        self.bytes_written = 0
        
        # 模拟串口配置
        self.bytesize = 8
        self.parity = 'N'
        self.stopbits = 1
        
        # 线程锁
        self.lock = threading.Lock()
        
    def open(self):
        """打开串口"""
        with self.lock:
            if not self.is_open:
                self.is_open = True
                logger.info(f"虚拟串口 {self.port_name} 已打开 (波特率: {self.baudrate})")
    
    def close(self):
        """关闭串口"""
        with self.lock:
            if self.is_open:
                self.is_open = False
                # 清空缓冲区
                while not self.read_buffer.empty():
                    try:
                        self.read_buffer.get_nowait()
                    except queue.Empty:
                        break
                logger.info(f"虚拟串口 {self.port_name} 已关闭")
    
    def write(self, data: bytes) -> int:
        """写入数据"""
        if not self.is_open:
            raise Exception("串口未打开")
        
        with self.lock:
            self.write_buffer.put(data)
            self.bytes_written += len(data)
            return len(data)
    
    def read(self, size: int = 1) -> bytes:
        """读取指定字节数的数据"""
        if not self.is_open:
            return b''
        
        result = b''
        end_time = time.time() + self.timeout
        
        while len(result) < size and time.time() < end_time:
            try:
                data = self.read_buffer.get(timeout=0.1)
                if isinstance(data, str):
                    data = data.encode('utf-8')
                result += data
                self.bytes_read += len(data)
                
                if len(result) >= size:
                    break
            except queue.Empty:
                continue
        
        return result[:size]
    
    def readline(self, size: int = -1) -> bytes:
        """读取一行数据"""
        if not self.is_open:
            return b''
        
        result = b''
        end_time = time.time() + self.timeout
        
        while time.time() < end_time:
            try:
                data = self.read_buffer.get(timeout=0.1)
                if isinstance(data, str):
                    data = data.encode('utf-8')
                
                result += data
                self.bytes_read += len(data)
                
                # 检查是否包含换行符
                if b'\n' in result:
                    line_end = result.find(b'\n') + 1
                    line = result[:line_end]
                    # 将剩余数据放回缓冲区
                    if len(result) > line_end:
                        self.read_buffer.put(result[line_end:])
                    return line
                    
                if size > 0 and len(result) >= size:
                    break
                    
            except queue.Empty:
                continue
        
        return result
    
    def put_data(self, data: Union[bytes, str]):
        """向读取缓冲区放入数据（模拟设备发送）"""
        if self.is_open:
            self.read_buffer.put(data)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'port_name': self.port_name,
            'baudrate': self.baudrate,
            'is_open': self.is_open,
            'bytes_read': self.bytes_read,
            'bytes_written': self.bytes_written,
            'buffer_size': self.read_buffer.qsize()
        }


class BaseEnhancedSensorDevice:
    """增强的传感器设备基类"""
    
    def __init__(self, device_id: str, serial_port: EnhancedVirtualSerialPort):
        self.device_id = device_id
        self.serial_port = serial_port
        self.running = False
        self.thread = None
        
        # 设备配置
        self.data_format = DataFormat.CSV
        self.interval = 5.0  # 发送间隔
        self.error_rate = 0.01  # 错误率
        
        # 传感器列表
        self.sensors: List[Dict[str, Any]] = []
        
        # 设备状态
        self.device_status = {
            'online': True,
            'battery_level': 100.0,
            'signal_strength': 100.0,
            'temperature': 25.0,
            'last_maintenance': datetime.now().isoformat(),
            'error_count': 0
        }
        
        # 统计信息
        self.message_count = 0
        self.error_count = 0
        
    def add_sensor(self, sensor_id: str, sensor_type: SensorType, 
                   value_range: tuple, unit: str, **kwargs):
        """添加传感器"""
        sensor_config = {
            'sensor_id': sensor_id,
            'sensor_type': sensor_type,
            'value_range': value_range,
            'unit': unit,
            'current_value': (value_range[0] + value_range[1]) / 2,
            'change_rate': kwargs.get('change_rate', 0.1),
            'precision': kwargs.get('precision', 2),
            'enabled': True
        }
        self.sensors.append(sensor_config)
        logger.info(f"设备 {self.device_id} 添加传感器: {sensor_id} ({sensor_type.value})")
    
    def start(self):
        """启动设备"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run)
            self.thread.daemon = True
            self.thread.start()
            logger.info(f"设备 {self.device_id} 已启动")
    
    def stop(self):
        """停止设备"""
        if self.running:
            self.running = False
            if self.thread:
                self.thread.join()
            logger.info(f"设备 {self.device_id} 已停止")
    
    def _run(self):
        """运行循环"""
        while self.running:
            try:
                # 生成传感器读数
                readings = self.generate_readings()
                
                # 格式化数据
                formatted_data = self.format_data(readings)
                
                # 发送数据
                if formatted_data:
                    self.serial_port.put_data(formatted_data)
                    self.message_count += 1
                    logger.debug(f"设备 {self.device_id} 发送数据: {formatted_data}")
                
                # 更新设备状态
                self.update_device_status()
                
                time.sleep(self.interval)
                
            except Exception as e:
                logger.error(f"设备 {self.device_id} 运行错误: {e}")
                self.error_count += 1
                time.sleep(1)
    
    def generate_readings(self) -> List[SensorReading]:
        """生成传感器读数"""
        readings = []
        
        for sensor in self.sensors:
            if not sensor['enabled']:
                continue
                
            try:
                # 模拟传感器值变化
                current_value = sensor['current_value']
                min_val, max_val = sensor['value_range']
                change_rate = sensor['change_rate']
                
                # 随机变化
                change = random.uniform(-change_rate, change_rate)
                new_value = current_value + change
                
                # 限制范围
                new_value = max(min_val, min(max_val, new_value))
                sensor['current_value'] = new_value
                
                # 应用精度
                precision = sensor['precision']
                if isinstance(precision, int):
                    new_value = round(new_value, precision)
                
                # 模拟数据质量
                quality = 1.0
                if random.random() < self.error_rate:
                    quality = random.uniform(0.5, 0.9)
                
                reading = SensorReading(
                    sensor_id=sensor['sensor_id'],
                    sensor_type=sensor['sensor_type'],
                    value=new_value,
                    unit=sensor['unit'],
                    timestamp=datetime.now(),
                    device_id=self.device_id,
                    quality=quality
                )
                
                readings.append(reading)
                
            except Exception as e:
                logger.error(f"传感器 {sensor['sensor_id']} 读数生成失败: {e}")
        
        return readings
    
    def format_data(self, readings: List[SensorReading]) -> bytes:
        """格式化数据"""
        if not readings:
            return b''
        
        try:
            if self.data_format == DataFormat.JSON:
                return self._format_json(readings)
            elif self.data_format == DataFormat.CSV:
                return self._format_csv(readings)
            elif self.data_format == DataFormat.BINARY:
                return self._format_binary(readings)
            else:
                return self._format_custom(readings)
        except Exception as e:
            logger.error(f"数据格式化失败: {e}")
            return b''
    
    def _format_json(self, readings: List[SensorReading]) -> bytes:
        """JSON格式"""
        data = {
            'device_id': self.device_id,
            'timestamp': datetime.now().isoformat(),
            'readings': [reading.to_dict() for reading in readings],
            'device_status': self.device_status.copy()
        }
        return json.dumps(data).encode('utf-8') + b'\n'
    
    def _format_csv(self, readings: List[SensorReading]) -> bytes:
        """CSV格式"""
        lines = []
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        for reading in readings:
            line = f"{self.device_id},{timestamp},{reading.sensor_id},{reading.sensor_type.value},{reading.value},{reading.unit},{reading.quality}"
            lines.append(line)
        
        return ('\n'.join(lines) + '\n').encode('utf-8')
    
    def _format_binary(self, readings: List[SensorReading]) -> bytes:
        """二进制格式"""
        data = bytearray()
        
        # 头部信息
        data.extend(struct.pack('!I', len(readings)))  # 读数数量
        data.extend(struct.pack('!I', int(time.time())))  # 时间戳
        
        # 传感器数据
        for reading in readings:
            sensor_id_bytes = reading.sensor_id.encode('utf-8')[:16].ljust(16, b'\0')
            data.extend(sensor_id_bytes)
            data.extend(struct.pack('!f', float(reading.value)))
            data.extend(struct.pack('!f', reading.quality))
        
        return bytes(data)
    
    def _format_custom(self, readings: List[SensorReading]) -> bytes:
        """自定义格式（类似Modbus）"""
        # 格式: DEV_ID:SENSOR_TYPE:VALUE:UNIT;
        parts = []
        for reading in readings:
            part = f"{self.device_id}:{reading.sensor_type.value}:{reading.value}:{reading.unit}"
            parts.append(part)
        
        return (';'.join(parts) + '\n').encode('utf-8')
    
    def update_device_status(self):
        """更新设备状态"""
        # 模拟电池电量下降
        self.device_status['battery_level'] -= random.uniform(0.01, 0.05)
        if self.device_status['battery_level'] < 0:
            self.device_status['battery_level'] = 0
        
        # 模拟信号强度变化
        self.device_status['signal_strength'] += random.uniform(-2, 2)
        self.device_status['signal_strength'] = max(0, min(100, self.device_status['signal_strength']))
        
        # 模拟设备温度
        self.device_status['temperature'] += random.uniform(-0.5, 0.5)
        self.device_status['temperature'] = max(0, min(70, self.device_status['temperature']))
        
        # 更新错误计数
        self.device_status['error_count'] = self.error_count
    
    def set_data_format(self, format_type: DataFormat):
        """设置数据格式"""
        self.data_format = format_type
        logger.info(f"设备 {self.device_id} 数据格式设置为: {format_type.value}")
    
    def set_interval(self, interval: float):
        """设置发送间隔"""
        self.interval = interval
        logger.info(f"设备 {self.device_id} 发送间隔设置为: {interval}s")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取设备统计信息"""
        return {
            'device_id': self.device_id,
            'running': self.running,
            'message_count': self.message_count,
            'error_count': self.error_count,
            'sensor_count': len(self.sensors),
            'device_status': self.device_status.copy()
        }


class SmartFarmDevice(BaseEnhancedSensorDevice):
    """智慧农场设备"""
    
    def __init__(self, device_id: str, serial_port: EnhancedVirtualSerialPort):
        super().__init__(device_id, serial_port)
        
        # 添加农业传感器
        self.add_sensor('temp_01', SensorType.TEMPERATURE, (15.0, 35.0), '°C', change_rate=0.5)
        self.add_sensor('hum_01', SensorType.HUMIDITY, (30.0, 90.0), '%', change_rate=2.0)
        self.add_sensor('light_01', SensorType.LIGHT, (0.0, 3000.0), 'lux', change_rate=50.0)
        self.add_sensor('soil_moisture_01', SensorType.SOIL_MOISTURE, (20.0, 80.0), '%', change_rate=1.0)
        self.add_sensor('soil_ph_01', SensorType.SOIL_PH, (5.5, 8.0), 'pH', change_rate=0.05)
        self.add_sensor('soil_ec_01', SensorType.SOIL_EC, (0.5, 3.0), 'mS/cm', change_rate=0.1)


class WeatherStationDevice(BaseEnhancedSensorDevice):
    """气象站设备"""
    
    def __init__(self, device_id: str, serial_port: EnhancedVirtualSerialPort):
        super().__init__(device_id, serial_port)
        
        # 添加气象传感器
        self.add_sensor('temp_01', SensorType.TEMPERATURE, (-20.0, 50.0), '°C', change_rate=0.5)
        self.add_sensor('hum_01', SensorType.HUMIDITY, (0.0, 100.0), '%', change_rate=2.0)
        self.add_sensor('pressure_01', SensorType.PRESSURE, (950.0, 1050.0), 'hPa', change_rate=1.0)
        self.add_sensor('wind_speed_01', SensorType.WIND_SPEED, (0.0, 20.0), 'm/s', change_rate=0.5)
        self.add_sensor('wind_dir_01', SensorType.WIND_DIRECTION, (0.0, 360.0), '°', change_rate=5.0)
        self.add_sensor('rain_01', SensorType.RAIN_LEVEL, (0.0, 50.0), 'mm', change_rate=0.2)
        self.add_sensor('uv_01', SensorType.UV_INDEX, (0.0, 12.0), 'UV', change_rate=0.1)


class EnvironmentalMonitorDevice(BaseEnhancedSensorDevice):
    """环境监测设备"""
    
    def __init__(self, device_id: str, serial_port: EnhancedVirtualSerialPort):
        super().__init__(device_id, serial_port)
        
        # 添加环境监测传感器
        self.add_sensor('temp_01', SensorType.TEMPERATURE, (18.0, 30.0), '°C', change_rate=0.3)
        self.add_sensor('hum_01', SensorType.HUMIDITY, (40.0, 80.0), '%', change_rate=1.5)
        self.add_sensor('co2_01', SensorType.CO2, (300.0, 1000.0), 'ppm', change_rate=10.0)
        self.add_sensor('noise_01', SensorType.NOISE, (30.0, 90.0), 'dB', change_rate=2.0)
        self.add_sensor('light_01', SensorType.LIGHT, (100.0, 1000.0), 'lux', change_rate=20.0)


class WaterManagementDevice(BaseEnhancedSensorDevice):
    """水管理设备"""
    
    def __init__(self, device_id: str, serial_port: EnhancedVirtualSerialPort):
        super().__init__(device_id, serial_port)
        
        # 添加水管理传感器
        self.add_sensor('water_level_01', SensorType.WATER_LEVEL, (0.0, 100.0), '%', change_rate=1.0)
        self.add_sensor('flow_rate_01', SensorType.FLOW_RATE, (0.0, 50.0), 'L/min', change_rate=2.0)
        self.add_sensor('pressure_01', SensorType.PRESSURE, (0.0, 10.0), 'bar', change_rate=0.1)
        self.add_sensor('temp_01', SensorType.TEMPERATURE, (10.0, 40.0), '°C', change_rate=0.5)


class EnhancedSerialDeviceManager:
    """增强的串口设备管理器"""
    
    def __init__(self):
        self.virtual_ports: Dict[str, EnhancedVirtualSerialPort] = {}
        self.devices: Dict[str, BaseEnhancedSensorDevice] = {}
        self.running = False
        
        # 管理器统计
        self.start_time = None
        self.total_messages = 0
        
    def create_virtual_port(self, port_name: str, baudrate: int = 9600, **kwargs) -> EnhancedVirtualSerialPort:
        """创建虚拟串口"""
        if port_name not in self.virtual_ports:
            port = EnhancedVirtualSerialPort(port_name, baudrate, **kwargs)
            self.virtual_ports[port_name] = port
            logger.info(f"创建虚拟串口: {port_name} (波特率: {baudrate})")
        return self.virtual_ports[port_name]
    
    def add_device(self, device: BaseEnhancedSensorDevice):
        """添加设备"""
        self.devices[device.device_id] = device
        logger.info(f"添加设备: {device.device_id}")
    
    def create_smart_farm_device(self, device_id: str, port_name: str, **kwargs) -> SmartFarmDevice:
        """创建智慧农场设备"""
        port = self.create_virtual_port(port_name, **kwargs)
        device = SmartFarmDevice(device_id, port)
        self.add_device(device)
        return device
    
    def create_weather_station(self, device_id: str, port_name: str, **kwargs) -> WeatherStationDevice:
        """创建气象站设备"""
        port = self.create_virtual_port(port_name, **kwargs)
        device = WeatherStationDevice(device_id, port)
        self.add_device(device)
        return device
    
    def create_environmental_monitor(self, device_id: str, port_name: str, **kwargs) -> EnvironmentalMonitorDevice:
        """创建环境监测设备"""
        port = self.create_virtual_port(port_name, **kwargs)
        device = EnvironmentalMonitorDevice(device_id, port)
        self.add_device(device)
        return device
    
    def create_water_management_device(self, device_id: str, port_name: str, **kwargs) -> WaterManagementDevice:
        """创建水管理设备"""
        port = self.create_virtual_port(port_name, **kwargs)
        device = WaterManagementDevice(device_id, port)
        self.add_device(device)
        return device
    
    def start_all_devices(self):
        """启动所有设备"""
        self.running = True
        self.start_time = datetime.now()
        
        # 打开所有串口
        for port in self.virtual_ports.values():
            port.open()
        
        # 启动所有设备
        for device in self.devices.values():
            device.start()
        
        logger.info(f"启动了 {len(self.devices)} 个设备")
    
    def stop_all_devices(self):
        """停止所有设备"""
        self.running = False
        
        # 停止所有设备
        for device in self.devices.values():
            device.stop()
        
        # 关闭所有串口
        for port in self.virtual_ports.values():
            port.close()
        
        logger.info("所有设备已停止")
    
    def get_device_stats(self) -> Dict[str, Any]:
        """获取设备统计信息"""
        stats = {
            'manager_running': self.running,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'uptime': str(datetime.now() - self.start_time) if self.start_time else None,
            'device_count': len(self.devices),
            'port_count': len(self.virtual_ports),
            'devices': {},
            'ports': {}
        }
        
        # 设备统计
        for device_id, device in self.devices.items():
            stats['devices'][device_id] = device.get_stats()
        
        # 串口统计
        for port_name, port in self.virtual_ports.items():
            stats['ports'][port_name] = port.get_stats()
        
        return stats
    
    def get_port(self, port_name: str) -> Optional[EnhancedVirtualSerialPort]:
        """获取虚拟串口"""
        return self.virtual_ports.get(port_name)
    
    def list_ports(self) -> List[str]:
        """列出所有虚拟串口"""
        return list(self.virtual_ports.keys())
    
    def set_global_interval(self, interval: float):
        """设置全局发送间隔"""
        for device in self.devices.values():
            device.set_interval(interval)
        logger.info(f"全局发送间隔设置为: {interval}s")
    
    def set_global_data_format(self, format_type: DataFormat):
        """设置全局数据格式"""
        for device in self.devices.values():
            device.set_data_format(format_type)
        logger.info(f"全局数据格式设置为: {format_type.value}")


def create_comprehensive_demo_setup(manager: EnhancedSerialDeviceManager):
    """创建综合演示设置"""
    logger.info("创建综合演示设备...")
    
    # 创建多个智慧农场设备
    farm_device_1 = manager.create_smart_farm_device("FARM_001", "COM1", baudrate=9600)
    farm_device_2 = manager.create_smart_farm_device("FARM_002", "COM2", baudrate=19200)
    
    # 创建气象站
    weather_station = manager.create_weather_station("WEATHER_001", "COM3", baudrate=9600)
    
    # 创建环境监测设备
    env_monitor = manager.create_environmental_monitor("ENV_001", "COM4", baudrate=9600)
    
    # 创建水管理设备
    water_device = manager.create_water_management_device("WATER_001", "COM5", baudrate=9600)
    
    # 设置不同的数据格式
    farm_device_1.set_data_format(DataFormat.CSV)
    farm_device_2.set_data_format(DataFormat.JSON)
    weather_station.set_data_format(DataFormat.CUSTOM)
    env_monitor.set_data_format(DataFormat.JSON)
    water_device.set_data_format(DataFormat.CSV)
    
    # 设置不同的发送间隔
    farm_device_1.set_interval(5.0)
    farm_device_2.set_interval(10.0)
    weather_station.set_interval(30.0)
    env_monitor.set_interval(15.0)
    water_device.set_interval(20.0)
    
    logger.info("综合演示设备创建完成")
    return {
        'farm_devices': [farm_device_1, farm_device_2],
        'weather_station': weather_station,
        'env_monitor': env_monitor,
        'water_device': water_device
    }


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='增强的串口设备模拟器')
    parser.add_argument('--interval', type=float, default=10.0, help='全局数据发送间隔(秒)')
    parser.add_argument('--format', choices=['json', 'csv', 'binary', 'custom'], 
                       default='csv', help='数据格式')
    parser.add_argument('--devices', nargs='+', 
                       choices=['farm', 'weather', 'env', 'water', 'all'],
                       default=['all'], help='要启动的设备类型')
    parser.add_argument('--stats-interval', type=float, default=60.0, help='统计信息显示间隔(秒)')
    
    args = parser.parse_args()
    
    # 创建设备管理器
    manager = EnhancedSerialDeviceManager()
    
    # 创建演示设备
    demo_devices = create_comprehensive_demo_setup(manager)
    
    # 设置全局配置
    data_format = DataFormat(args.format)
    manager.set_global_data_format(data_format)
    manager.set_global_interval(args.interval)
    
    try:
        # 启动所有设备
        manager.start_all_devices()
        
        logger.info("增强的串口设备模拟器正在运行...")
        logger.info(f"数据格式: {data_format.value}")
        logger.info(f"发送间隔: {args.interval}s")
        logger.info("可用的虚拟串口:")
        for port in manager.list_ports():
            logger.info(f"  - {port}")
        
        logger.info("按 Ctrl+C 停止模拟器")
        
        # 定期显示统计信息
        last_stats_time = time.time()
        
        while True:
            time.sleep(1)
            
            # 显示统计信息
            if time.time() - last_stats_time >= args.stats_interval:
                stats = manager.get_device_stats()
                logger.info("=== 设备统计信息 ===")
                logger.info(f"运行时间: {stats['uptime']}")
                logger.info(f"设备数量: {stats['device_count']}")
                
                for device_id, device_stats in stats['devices'].items():
                    logger.info(f"{device_id}: 消息数={device_stats['message_count']}, 错误数={device_stats['error_count']}")
                
                last_stats_time = time.time()
            
    except KeyboardInterrupt:
        logger.info("接收到停止信号")
        
    finally:
        manager.stop_all_devices()
        logger.info("增强的串口设备模拟器已停止")


if __name__ == "__main__":
    main()
