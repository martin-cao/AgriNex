"""
MQTT adapter for AgriNex sensor client.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Optional, Callable, Dict, Any
import paho.mqtt.client as mqtt
from ..core.config import Config, MQTTConfig
from ..core.sensor_data import SensorData


class MQTTAdapter:
    """MQTT communication adapter."""
    
    def __init__(self, config: Config):
        self.config = config
        self.mqtt_config = config.mqtt
        self.client_id = config.client_id
        self.logger = logging.getLogger(__name__)
        
        # MQTT client setup
        self.client = mqtt.Client(client_id=self.client_id)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.client.on_publish = self._on_publish
        
        # Connection state
        self.connected = False
        self.connection_callbacks: list[Callable] = []
        self.message_callbacks: list[Callable] = []
        
        # Statistics
        self.messages_sent = 0
        self.messages_failed = 0
        self.last_message_time: Optional[datetime] = None
        
    def add_connection_callback(self, callback: Callable[[bool], None]) -> None:
        """Add callback for connection state changes."""
        self.connection_callbacks.append(callback)
        
    def add_message_callback(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """Add callback for incoming messages."""
        self.message_callbacks.append(callback)
    
    def _on_connect(self, client, userdata, flags, rc):
        """Handle MQTT connection."""
        if rc == 0:
            self.connected = True
            self.logger.info(f"Connected to MQTT broker at {self.mqtt_config.host}:{self.mqtt_config.port}")
            
            # Subscribe to control topics
            control_topic = f"sensors/{self.client_id}/control"
            client.subscribe(control_topic, qos=self.mqtt_config.qos)
            self.logger.info(f"Subscribed to control topic: {control_topic}")
            
            # Notify callbacks
            for callback in self.connection_callbacks:
                try:
                    callback(True)
                except Exception as e:
                    self.logger.error(f"Error in connection callback: {e}")
        else:
            self.connected = False
            self.logger.error(f"Failed to connect to MQTT broker. Return code: {rc}")
            
            # Notify callbacks
            for callback in self.connection_callbacks:
                try:
                    callback(False)
                except Exception as e:
                    self.logger.error(f"Error in connection callback: {e}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Handle MQTT disconnection."""
        self.connected = False
        if rc != 0:
            self.logger.warning(f"Unexpected MQTT disconnection. Return code: {rc}")
        else:
            self.logger.info("Disconnected from MQTT broker")
            
        # Notify callbacks
        for callback in self.connection_callbacks:
            try:
                callback(False)
            except Exception as e:
                self.logger.error(f"Error in connection callback: {e}")
    
    def _on_message(self, client, userdata, msg):
        """Handle incoming MQTT messages."""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            self.logger.debug(f"Received message on topic {topic}: {payload}")
            
            # Notify callbacks
            for callback in self.message_callbacks:
                try:
                    callback(topic, payload)
                except Exception as e:
                    self.logger.error(f"Error in message callback: {e}")
                    
        except json.JSONDecodeError:
            self.logger.error(f"Failed to decode message payload: {msg.payload}")
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
    
    def _on_publish(self, client, userdata, mid):
        """Handle message publish confirmation."""
        self.logger.debug(f"Message published successfully. Message ID: {mid}")
    
    async def connect(self) -> bool:
        """Connect to MQTT broker."""
        try:
            # Set credentials if provided
            if self.mqtt_config.username and self.mqtt_config.password:
                self.client.username_pw_set(
                    self.mqtt_config.username, 
                    self.mqtt_config.password
                )
            
            # Connect to broker
            self.client.connect(
                self.mqtt_config.host,
                self.mqtt_config.port,
                self.mqtt_config.keepalive
            )
            
            # Start network loop
            self.client.loop_start()
            
            # Wait for connection (with timeout)
            for _ in range(50):  # 5 seconds timeout
                if self.connected:
                    return True
                await asyncio.sleep(0.1)
                
            self.logger.error("Timeout waiting for MQTT connection")
            return False
            
        except Exception as e:
            self.logger.error(f"Error connecting to MQTT broker: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from MQTT broker."""
        try:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
            self.logger.info("Disconnected from MQTT broker")
        except Exception as e:
            self.logger.error(f"Error disconnecting from MQTT broker: {e}")
    
    async def send_sensor_data(self, sensor_data: SensorData) -> bool:
        """Send sensor data to MQTT broker."""
        if not self.connected:
            self.logger.warning("Not connected to MQTT broker")
            return False
        
        try:
            # Send to numeric topic (for compatibility)
            numeric_topic = self.config.get_mqtt_topic('numeric')
            numeric_payload = sensor_data.get_numeric_values()
            
            result = self.client.publish(
                numeric_topic,
                json.dumps(numeric_payload),
                qos=self.mqtt_config.qos,
                retain=self.mqtt_config.retain
            )
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                self.messages_sent += 1
                self.last_message_time = datetime.now()
                self.logger.debug(f"Sent numeric data to {numeric_topic}: {numeric_payload}")
                
                # Also send detailed data if configured
                if self.config.sensor.include_metadata:
                    data_topic = self.config.get_mqtt_topic('sensor_data')
                    data_payload = sensor_data.to_mqtt_payload()
                    
                    result2 = self.client.publish(
                        data_topic,
                        json.dumps(data_payload),
                        qos=self.mqtt_config.qos,
                        retain=self.mqtt_config.retain
                    )
                    
                    if result2.rc == mqtt.MQTT_ERR_SUCCESS:
                        self.logger.debug(f"Sent detailed data to {data_topic}")
                
                return True
            else:
                self.messages_failed += 1
                self.logger.error(f"Failed to publish message. Return code: {result.rc}")
                return False
                
        except Exception as e:
            self.messages_failed += 1
            self.logger.error(f"Error sending sensor data: {e}")
            return False
    
    async def send_status(self, status: Dict[str, Any]) -> bool:
        """Send status information."""
        if not self.connected:
            return False
        
        try:
            topic = self.config.get_mqtt_topic('status')
            payload = {
                'client_id': self.client_id,
                'timestamp': datetime.now().isoformat(),
                'status': status
            }
            
            result = self.client.publish(
                topic,
                json.dumps(payload),
                qos=self.mqtt_config.qos,
                retain=True  # Status messages should be retained
            )
            
            return result.rc == mqtt.MQTT_ERR_SUCCESS
            
        except Exception as e:
            self.logger.error(f"Error sending status: {e}")
            return False
    
    async def send_error(self, error_info: Dict[str, Any]) -> bool:
        """Send error information."""
        if not self.connected:
            return False
        
        try:
            topic = self.config.get_mqtt_topic('error')
            payload = {
                'client_id': self.client_id,
                'timestamp': datetime.now().isoformat(),
                'error': error_info
            }
            
            result = self.client.publish(
                topic,
                json.dumps(payload),
                qos=2,  # Ensure delivery for errors
                retain=False
            )
            
            return result.rc == mqtt.MQTT_ERR_SUCCESS
            
        except Exception as e:
            self.logger.error(f"Error sending error info: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get adapter statistics."""
        return {
            'connected': self.connected,
            'messages_sent': self.messages_sent,
            'messages_failed': self.messages_failed,
            'last_message_time': self.last_message_time.isoformat() if self.last_message_time else None,
            'broker_host': self.mqtt_config.host,
            'broker_port': self.mqtt_config.port
        }
