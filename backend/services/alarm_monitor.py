# backend/services/alarm_monitor.py
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from models.reading import Reading
from models.sensor import Sensor
from services.alarm_service import AlarmService
from extensions import db
from flask import Flask

logger = logging.getLogger(__name__)

class AlarmMonitor:
    """告警监控服务"""
    
    def __init__(self):
        self.is_running = False
        self.check_interval = 30  # 检查间隔（秒）
        self.last_check_time = {}  # 记录每个传感器的最后检查时间
        self.app: Optional[Flask] = None  # Flask应用实例
    
    async def start(self):
        """启动告警监控"""
        self.is_running = True
        logger.info("Alarm monitor started")
        
        while self.is_running:
            try:
                await self._check_all_sensors()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in alarm monitor: {e}")
                await asyncio.sleep(5)  # 出错后短暂休息
    
    def stop(self):
        """停止告警监控"""
        self.is_running = False
        logger.info("Alarm monitor stopped")
    
    async def _check_all_sensors(self):
        """检查所有传感器的最新读数"""
        try:
            if self.app is None:
                logger.error("Flask app not initialized for alarm monitor")
                return
                
            with self.app.app_context():
                # 获取所有活跃的传感器
                sensors = Sensor.query.filter_by(is_active=True).all()
                
                for sensor in sensors:
                    await self._check_sensor_readings(sensor.id)
        except Exception as e:
            logger.error(f"Error checking sensors: {e}")
    
    async def _check_sensor_readings(self, sensor_id: int):
        """检查特定传感器的读数"""
        try:
            if self.app is None:
                logger.error("Flask app not initialized for alarm monitor")
                return
                
            with self.app.app_context():
                # 获取最后检查时间
                last_check = self.last_check_time.get(sensor_id, datetime.utcnow() - timedelta(minutes=5))
                
                # 获取自上次检查以来的新读数
                new_readings = Reading.query.filter(
                    Reading.sensor_id == sensor_id,
                    Reading.timestamp > last_check,
                    Reading.data_type == 'numeric'
                ).order_by(Reading.timestamp.asc()).all()
                
                if not new_readings:
                    return
                
                # 逐个检查新读数
                for reading in new_readings:
                    if reading.numeric_value is not None:
                        # 检查并触发告警
                        triggered_alarms = AlarmService.check_and_trigger_alarms(
                            sensor_id=sensor_id,
                            value=reading.numeric_value,
                            reading_timestamp=reading.timestamp
                        )
                        
                        if triggered_alarms:
                            logger.info(f"Triggered {len(triggered_alarms)} alarms for sensor {sensor_id}")
                
                # 更新最后检查时间
                self.last_check_time[sensor_id] = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Error checking sensor {sensor_id}: {e}")

    def check_reading_immediately(self, sensor_id: int, value: float, timestamp: Optional[datetime] = None):
        """立即检查单个读数（用于实时触发）"""        
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        try:
            if self.app is None:
                logger.error("Flask app not initialized for alarm monitor")
                return []
                
            with self.app.app_context():
                triggered_alarms = AlarmService.check_and_trigger_alarms(
                    sensor_id=sensor_id,
                    value=value,
                    reading_timestamp=timestamp
                )
                
                if triggered_alarms:
                    logger.info(f"Immediately triggered {len(triggered_alarms)} alarms for sensor {sensor_id}")
                    
                return triggered_alarms
        except Exception as e:
            logger.error(f"Error in immediate alarm check: {e}")
            return []

# 全局实例
alarm_monitor = AlarmMonitor()
