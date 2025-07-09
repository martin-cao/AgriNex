# backend/services/alarm_startup.py
import asyncio
import logging
from services.alarm_monitor import alarm_monitor

logger = logging.getLogger(__name__)

async def start_alarm_monitor():
    """启动告警监控服务"""
    try:
        logger.info("Starting alarm monitor service...")
        await alarm_monitor.start()
    except Exception as e:
        logger.error(f"Failed to start alarm monitor: {e}")

def stop_alarm_monitor():
    """停止告警监控服务"""
    try:
        logger.info("Stopping alarm monitor service...")
        alarm_monitor.stop()
    except Exception as e:
        logger.error(f"Failed to stop alarm monitor: {e}")

# 在应用启动时调用
def init_alarm_services(app):
    """初始化告警服务"""
    try:
        import threading
        
        # 在启动线程之前设置app实例
        alarm_monitor.app = app
        
        def run_alarm_monitor():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(start_alarm_monitor())
        
        alarm_thread = threading.Thread(target=run_alarm_monitor, daemon=True)
        alarm_thread.start()
        
        logger.info("Alarm services initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize alarm services: {e}")
