"""
HTTP Health Service for sensor client monitoring.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from aiohttp import web, ClientSession
import aiohttp


class HTTPHealthService:
    """HTTP service providing health checks and status monitoring."""
    
    def __init__(self, sensor_service, port: int = 8080):
        self.sensor_service = sensor_service
        self.port = port
        self.logger = logging.getLogger(__name__)
        self.app = None
        self.runner = None
        self.site = None
        
    async def start(self):
        """Start the HTTP service."""
        try:
            self.logger.info(f"Starting HTTP health service on port {self.port}")
            
            # Create aiohttp application
            self.app = web.Application()
            
            # Add routes
            self.app.router.add_get('/health', self.health_check)
            self.app.router.add_get('/status', self.status_info)
            self.app.router.add_get('/metrics', self.metrics_info)
            
            # Start the server
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            
            self.site = web.TCPSite(self.runner, '0.0.0.0', self.port)
            await self.site.start()
            
            self.logger.info(f"HTTP health service started on http://0.0.0.0:{self.port}")
            
        except Exception as e:
            self.logger.error(f"Error starting HTTP service: {e}")
            raise
    
    async def stop(self):
        """Stop the HTTP service."""
        try:
            self.logger.info("Stopping HTTP health service")
            
            if self.site:
                await self.site.stop()
            
            if self.runner:
                await self.runner.cleanup()
                
            self.logger.info("HTTP health service stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping HTTP service: {e}")
    
    async def health_check(self, request):
        """Health check endpoint."""
        try:
            # Check if sensor service is running
            is_healthy = self.sensor_service.running if self.sensor_service else False
            
            # Check MQTT connection
            mqtt_connected = False
            if self.sensor_service and hasattr(self.sensor_service, 'mqtt_adapter'):
                mqtt_connected = self.sensor_service.mqtt_adapter.connected
            
            # Check serial connection
            serial_connected = False
            if self.sensor_service and hasattr(self.sensor_service, 'serial_adapter'):
                serial_connected = self.sensor_service.serial_adapter.connected
            
            health_data = {
                'status': 'healthy' if is_healthy else 'unhealthy',
                'timestamp': datetime.now().isoformat(),
                'service_running': is_healthy,
                'mqtt_connected': mqtt_connected,
                'serial_connected': serial_connected,
                'uptime_seconds': self._get_uptime(),
                'client_id': getattr(self.sensor_service.config, 'client_id', 'unknown') if self.sensor_service else 'unknown'
            }
            
            status_code = 200 if is_healthy else 503
            return web.json_response(health_data, status=status_code)
            
        except Exception as e:
            self.logger.error(f"Error in health check: {e}")
            return web.json_response({
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }, status=500)
    
    async def status_info(self, request):
        """Detailed status information endpoint."""
        try:
            if not self.sensor_service:
                return web.json_response({
                    'error': 'Sensor service not available'
                }, status=503)
            
            status_data = {
                'service': {
                    'running': self.sensor_service.running,
                    'start_time': self.sensor_service.start_time.isoformat() if self.sensor_service.start_time else None,
                    'uptime_seconds': self._get_uptime(),
                    'client_id': getattr(self.sensor_service.config, 'client_id', 'unknown')
                },
                'statistics': {
                    'total_readings': getattr(self.sensor_service, 'total_readings', 0),
                    'total_transmissions': getattr(self.sensor_service, 'total_transmissions', 0),
                    'error_count': getattr(self.sensor_service, 'error_count', 0)
                },
                'connections': {
                    'mqtt': {
                        'connected': self.sensor_service.mqtt_adapter.connected if hasattr(self.sensor_service, 'mqtt_adapter') else False,
                        'host': getattr(self.sensor_service.config.mqtt, 'host', 'unknown') if hasattr(self.sensor_service, 'config') else 'unknown',
                        'port': getattr(self.sensor_service.config.mqtt, 'port', 'unknown') if hasattr(self.sensor_service, 'config') else 'unknown'
                    },
                    'serial': {
                        'connected': self.sensor_service.serial_adapter.connected if hasattr(self.sensor_service, 'serial_adapter') else False,
                        'simulation_mode': getattr(self.sensor_service.config.serial, 'simulation_mode', True) if hasattr(self.sensor_service, 'config') else True
                    }
                },
                'timestamp': datetime.now().isoformat()
            }
            
            return web.json_response(status_data)
            
        except Exception as e:
            self.logger.error(f"Error getting status info: {e}")
            return web.json_response({
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }, status=500)
    
    async def metrics_info(self, request):
        """Metrics endpoint for monitoring."""
        try:
            if not self.sensor_service:
                return web.json_response({
                    'error': 'Sensor service not available'
                }, status=503)
            
            metrics = {
                'sensor_readings_total': getattr(self.sensor_service, 'total_readings', 0),
                'sensor_transmissions_total': getattr(self.sensor_service, 'total_transmissions', 0),
                'sensor_errors_total': getattr(self.sensor_service, 'error_count', 0),
                'sensor_uptime_seconds': self._get_uptime(),
                'sensor_service_running': 1 if self.sensor_service.running else 0,
                'mqtt_connected': 1 if (hasattr(self.sensor_service, 'mqtt_adapter') and self.sensor_service.mqtt_adapter.connected) else 0,
                'serial_connected': 1 if (hasattr(self.sensor_service, 'serial_adapter') and self.sensor_service.serial_adapter.connected) else 0
            }
            
            # Convert to Prometheus format
            prometheus_output = []
            for key, value in metrics.items():
                prometheus_output.append(f"# TYPE {key} gauge")
                prometheus_output.append(f"{key} {value}")
            
            return web.Response(
                text='\n'.join(prometheus_output) + '\n',
                content_type='text/plain'
            )
            
        except Exception as e:
            self.logger.error(f"Error getting metrics: {e}")
            return web.Response(
                text=f"# Error getting metrics: {e}\n",
                content_type='text/plain',
                status=500
            )
    
    def _get_uptime(self) -> float:
        """Get service uptime in seconds."""
        if self.sensor_service and self.sensor_service.start_time:
            return (datetime.now() - self.sensor_service.start_time).total_seconds()
        return 0.0
