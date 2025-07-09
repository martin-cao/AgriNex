#!/usr/bin/env python3
"""
AgriNex 传感器客户端启动器
统一的启动接口和配置管理
"""

import os
import sys
import json
import logging
import argparse
import asyncio
import signal
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# 添加项目路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(current_dir))

from enhanced_mqtt_client import EnhancedMQTTSensorClient

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(current_dir / 'sensor_client.log')
    ]
)
logger = logging.getLogger(__name__)


class SensorClientLauncher:
    """传感器客户端启动器"""
    
    def __init__(self):
        self.client: Optional[EnhancedMQTTSensorClient] = None
        self.running = False
        self.config_file = current_dir / 'client_config.json'
        self.default_config = {
            'mqtt': {
                'host': 'localhost',
                'port': 1883,
                'username': '',
                'password': '',
                'keepalive': 60
            },
            'client': {
                'id': None,  # 自动生成
                'scan_interval': 30.0,
                'image_interval': 60.0,
                'retry_interval': 10.0,
                'max_retries': 3
            },
            'features': {
                'camera_enabled': False,
                'auto_reconnect': True,
                'debug_mode': False
            },
            'logging': {
                'level': 'INFO',
                'file': 'sensor_client.log'
            }
        }
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    logger.info(f"配置文件加载成功: {self.config_file}")
                    return self.merge_config(self.default_config, config)
            else:
                logger.info("配置文件不存在，使用默认配置")
                return self.default_config.copy()
        except Exception as e:
            logger.error(f"配置文件加载失败: {e}")
            return self.default_config.copy()
    
    def save_config(self, config: Dict[str, Any]):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            logger.info(f"配置文件保存成功: {self.config_file}")
        except Exception as e:
            logger.error(f"配置文件保存失败: {e}")
    
    def merge_config(self, default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """合并配置"""
        result = default.copy()
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self.merge_config(result[key], value)
            else:
                result[key] = value
        return result
    
    def create_client_id(self) -> str:
        """创建客户端ID"""
        import uuid
        import socket
        
        hostname = socket.gethostname()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = uuid.uuid4().hex[:8]
        
        return f"agrinex_sensor_{hostname}_{timestamp}_{unique_id}"
    
    def setup_logging(self, config: Dict[str, Any]):
        """设置日志配置"""
        log_config = config.get('logging', {})
        
        # 设置日志级别
        level = getattr(logging, log_config.get('level', 'INFO').upper())
        logging.getLogger().setLevel(level)
        
        # 如果是调试模式，设置详细日志
        if config.get('features', {}).get('debug_mode', False):
            logging.getLogger().setLevel(logging.DEBUG)
            logger.info("调试模式已启用")
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """验证配置"""
        try:
            # 检查必需的配置项
            required_mqtt = ['host', 'port']
            mqtt_config = config.get('mqtt', {})
            
            for key in required_mqtt:
                if key not in mqtt_config:
                    logger.error(f"缺少必需的MQTT配置: {key}")
                    return False
            
            # 验证端口号
            port = mqtt_config.get('port')
            if not isinstance(port, int) or port <= 0 or port > 65535:
                logger.error(f"无效的MQTT端口: {port}")
                return False
            
            # 验证间隔时间
            client_config = config.get('client', {})
            intervals = ['scan_interval', 'image_interval', 'retry_interval']
            
            for interval in intervals:
                value = client_config.get(interval)
                if value is not None and (not isinstance(value, (int, float)) or value <= 0):
                    logger.error(f"无效的间隔时间配置: {interval}={value}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"配置验证失败: {e}")
            return False
    
    def print_config_info(self, config: Dict[str, Any]):
        """打印配置信息"""
        logger.info("=== 传感器客户端配置信息 ===")
        logger.info(f"客户端ID: {config['client']['id']}")
        logger.info(f"MQTT服务器: {config['mqtt']['host']}:{config['mqtt']['port']}")
        logger.info(f"扫描间隔: {config['client']['scan_interval']}s")
        logger.info(f"图像间隔: {config['client']['image_interval']}s")
        logger.info(f"摄像头: {'启用' if config['features']['camera_enabled'] else '禁用'}")
        logger.info(f"自动重连: {'启用' if config['features']['auto_reconnect'] else '禁用'}")
        logger.info(f"调试模式: {'启用' if config['features']['debug_mode'] else '禁用'}")
        logger.info("========================")
    
    def create_client(self, config: Dict[str, Any]) -> EnhancedMQTTSensorClient:
        """创建客户端实例"""
        client_id = config['client']['id']
        mqtt_config = config['mqtt']
        
        # 创建客户端
        client = EnhancedMQTTSensorClient(client_id, mqtt_config)
        
        # 应用配置
        client.scan_interval = config['client']['scan_interval']
        client.image_interval = config['client']['image_interval']
        client.retry_interval = config['client']['retry_interval']
        client.max_retries = config['client']['max_retries']
        client.camera_enabled = config['features']['camera_enabled']
        
        return client
    
    def setup_signal_handlers(self):
        """设置信号处理器"""
        def signal_handler(signum, frame):
            logger.info(f"接收到信号 {signum}，正在停止...")
            self.running = False
            if self.client:
                asyncio.create_task(self.client.stop())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def start_client(self, config: Dict[str, Any]):
        """启动客户端"""
        try:
            # 创建客户端
            self.client = self.create_client(config)
            
            # 打印启动信息
            logger.info("🚀 启动AgriNex传感器客户端...")
            self.print_config_info(config)
            
            # 启动客户端
            self.running = True
            await self.client.start()
            
        except Exception as e:
            logger.error(f"客户端启动失败: {e}")
            raise
    
    async def run_with_auto_reconnect(self, config: Dict[str, Any]):
        """带自动重连的运行"""
        auto_reconnect = config.get('features', {}).get('auto_reconnect', True)
        retry_interval = config.get('client', {}).get('retry_interval', 10.0)
        
        while self.running:
            try:
                await self.start_client(config)
                
            except KeyboardInterrupt:
                logger.info("用户中断程序")
                break
                
            except Exception as e:
                logger.error(f"客户端运行异常: {e}")
                
                if not auto_reconnect:
                    logger.info("自动重连已禁用，程序退出")
                    break
                
                if self.running:
                    logger.info(f"将在 {retry_interval} 秒后重试...")
                    await asyncio.sleep(retry_interval)
                else:
                    break
    
    def run(self, args: argparse.Namespace):
        """运行客户端"""
        try:
            # 加载配置
            config = self.load_config()
            
            # 命令行参数覆盖配置
            if args.client_id:
                config['client']['id'] = args.client_id
            if args.mqtt_host:
                config['mqtt']['host'] = args.mqtt_host
            if args.mqtt_port:
                config['mqtt']['port'] = args.mqtt_port
            if args.scan_interval:
                config['client']['scan_interval'] = args.scan_interval
            if args.image_interval:
                config['client']['image_interval'] = args.image_interval
            if args.camera:
                config['features']['camera_enabled'] = True
            if args.debug:
                config['features']['debug_mode'] = True
            if args.no_reconnect:
                config['features']['auto_reconnect'] = False
            
            # 生成客户端ID（如果未设置）
            if not config['client']['id']:
                config['client']['id'] = self.create_client_id()
            
            # 设置日志
            self.setup_logging(config)
            
            # 验证配置
            if not self.validate_config(config):
                logger.error("配置验证失败，程序退出")
                return 1
            
            # 保存配置
            if args.save_config:
                self.save_config(config)
                logger.info("配置已保存")
            
            # 设置信号处理器
            self.setup_signal_handlers()
            
            # 运行客户端
            asyncio.run(self.run_with_auto_reconnect(config))
            
            return 0
            
        except Exception as e:
            logger.error(f"程序运行失败: {e}")
            return 1
        finally:
            logger.info("程序结束")


def create_sample_config():
    """创建示例配置文件"""
    launcher = SensorClientLauncher()
    config = launcher.default_config.copy()
    
    # 添加注释说明
    config['_comments'] = {
        'mqtt': 'MQTT服务器配置',
        'client': '客户端行为配置',
        'features': '功能开关配置',
        'logging': '日志配置'
    }
    
    config_file = Path(__file__).parent / 'client_config.json'
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"示例配置文件已创建: {config_file}")
    except Exception as e:
        print(f"创建配置文件失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='AgriNex 传感器客户端启动器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python sensor_launcher.py                    # 使用默认配置启动
  python sensor_launcher.py --camera           # 启用摄像头功能
  python sensor_launcher.py --debug            # 启用调试模式
  python sensor_launcher.py --save-config     # 保存当前配置
  python sensor_launcher.py --create-config   # 创建示例配置文件
        """
    )
    
    # 基本配置
    parser.add_argument('--client-id', help='客户端ID')
    parser.add_argument('--mqtt-host', help='MQTT服务器地址')
    parser.add_argument('--mqtt-port', type=int, help='MQTT服务器端口')
    
    # 行为配置
    parser.add_argument('--scan-interval', type=float, help='端口扫描间隔(秒)')
    parser.add_argument('--image-interval', type=float, help='图像采集间隔(秒)')
    
    # 功能开关
    parser.add_argument('--camera', action='store_true', help='启用摄像头功能')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    parser.add_argument('--no-reconnect', action='store_true', help='禁用自动重连')
    
    # 配置管理
    parser.add_argument('--save-config', action='store_true', help='保存配置到文件')
    parser.add_argument('--create-config', action='store_true', help='创建示例配置文件')
    
    args = parser.parse_args()
    
    # 创建配置文件
    if args.create_config:
        create_sample_config()
        return 0
    
    # 启动客户端
    launcher = SensorClientLauncher()
    return launcher.run(args)


if __name__ == "__main__":
    sys.exit(main())
