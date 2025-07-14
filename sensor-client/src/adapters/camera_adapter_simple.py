"""
Camera adapter for capturing images and videos from device camera.
支持从设备摄像头捕获图片和视频。
简化版本，主要支持模拟模式。
"""

import asyncio
import logging
import base64
import tempfile
import os
from datetime import datetime
from typing import Optional, Dict, Any, Callable, List
from pathlib import Path
import json

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    cv2 = None

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None

from ..core.config import Config


class CameraAdapter:
    """Camera adapter for image and video capture."""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Camera settings
        self.camera_index = getattr(config, 'camera_index', 0)
        self.capture_width = getattr(config, 'capture_width', 640)
        self.capture_height = getattr(config, 'capture_height', 480)
        self.capture_fps = getattr(config, 'capture_fps', 30)
        
        # Image/Video settings
        self.image_quality = getattr(config, 'image_quality', 85)  # JPEG quality 1-100
        self.video_duration = getattr(config, 'video_duration', 10)  # seconds
        self.video_codec = getattr(config, 'video_codec', 'mp4v')
        
        # Operating mode - force simulation if cv2 not available
        self.simulation_mode = getattr(config, 'simulation_mode', True) or not CV2_AVAILABLE
        if not CV2_AVAILABLE and not getattr(config, 'simulation_mode', True):
            self.logger.warning("OpenCV not available, forcing simulation mode")
        
        # Camera object
        self.camera = None
        self.is_initialized = False
        
        # Callbacks
        self.data_callbacks: List[Callable] = []
        self.error_callbacks: List[Callable] = []
        
        # Statistics
        self.total_captures = 0
        self.total_errors = 0
    
    def add_data_callback(self, callback: Callable):
        """Add callback for captured data."""
        self.data_callbacks.append(callback)
    
    def add_error_callback(self, callback: Callable):
        """Add callback for errors."""
        self.error_callbacks.append(callback)
    
    def _notify_data(self, data: Dict[str, Any]):
        """Notify all data callbacks."""
        for callback in self.data_callbacks:
            try:
                callback(data)
            except Exception as e:
                self.logger.error(f"Error in data callback: {e}")
    
    def _notify_error(self, context: str, error: Exception):
        """Notify all error callbacks."""
        for callback in self.error_callbacks:
            try:
                callback(context, error)
            except Exception as e:
                self.logger.error(f"Error in error callback: {e}")
    
    async def initialize(self) -> bool:
        """Initialize camera connection."""
        try:
            if self.simulation_mode:
                self.logger.info("Camera adapter initialized in simulation mode")
                self.is_initialized = True
                return True
            
            if not CV2_AVAILABLE:
                self.logger.warning("OpenCV not available, falling back to simulation mode")
                self.simulation_mode = True
                self.is_initialized = True
                return True
            
            # Initialize real camera
            if cv2 is None:
                raise Exception("OpenCV not available")
                
            self.camera = cv2.VideoCapture(self.camera_index)
            
            if not self.camera.isOpened():
                self.logger.warning(f"Cannot open camera {self.camera_index}, falling back to simulation")
                self.simulation_mode = True
                self.camera = None
                self.is_initialized = True
                return True
            
            # Set camera properties
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.capture_width)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.capture_height)
            self.camera.set(cv2.CAP_PROP_FPS, self.capture_fps)
            
            # Test capture
            ret, frame = self.camera.read()
            if not ret:
                self.logger.warning("Cannot capture test frame, falling back to simulation")
                self.camera.release()
                self.camera = None
                self.simulation_mode = True
                self.is_initialized = True
                return True
            
            self.logger.info(f"Real camera initialized: {self.capture_width}x{self.capture_height} @ {self.capture_fps}fps")
            self.is_initialized = True
            return True
            
        except Exception as e:
            self.logger.warning(f"Camera initialization failed, using simulation: {e}")
            self.simulation_mode = True
            self.camera = None
            self.is_initialized = True
            return True
    
    async def capture_image(self, sensor_id: str = "camera_001") -> Optional[Dict[str, Any]]:
        """Capture a single image."""
        try:
            if self.simulation_mode or not CV2_AVAILABLE:
                return await self._capture_simulated_image(sensor_id)
            
            if not self.is_initialized or self.camera is None:
                raise Exception("Camera not initialized")
            
            # Capture frame
            ret, frame = self.camera.read()
            if not ret:
                # Fall back to simulation
                self.logger.warning("Frame capture failed, using simulation")
                return await self._capture_simulated_image(sensor_id)
            
            # Encode image to JPEG
            if cv2 is None:
                raise Exception("OpenCV not available for encoding")
                
            encode_params = [cv2.IMWRITE_JPEG_QUALITY, self.image_quality]
            success, buffer = cv2.imencode('.jpg', frame, encode_params)
            
            if not success:
                raise Exception("Failed to encode image")
            
            # Convert to base64
            image_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # Create data structure
            timestamp = datetime.now()
            image_data = {
                'sensor_id': sensor_id,
                'timestamp': timestamp.isoformat(),
                'type': 'image',
                'data': {
                    'format': 'jpeg',
                    'width': self.capture_width,
                    'height': self.capture_height,
                    'quality': self.image_quality,
                    'size_bytes': len(buffer),
                    'image_base64': image_base64
                },
                'metadata': {
                    'capture_device': f"camera_{self.camera_index}",
                    'capture_time': timestamp.isoformat(),
                    'location': getattr(self.config, 'location', 'greenhouse_001')
                }
            }
            
            self.total_captures += 1
            self.logger.debug(f"Captured real image: {len(buffer)} bytes")
            
            # Notify callbacks
            self._notify_data(image_data)
            
            return image_data
            
        except Exception as e:
            self.total_errors += 1
            self.logger.warning(f"Real camera error, falling back to simulation: {e}")
            return await self._capture_simulated_image(sensor_id)
    
    async def capture_video(self, duration: Optional[int] = None, sensor_id: str = "camera_001") -> Optional[Dict[str, Any]]:
        """Capture a video for specified duration."""
        # For now, always use simulation for video to avoid complexity
        capture_duration = duration if duration is not None else self.video_duration
        return await self._capture_simulated_video(sensor_id, capture_duration)
    
    async def _capture_simulated_image(self, sensor_id: str) -> Dict[str, Any]:
        """Capture simulated image data."""
        try:
            # Generate simple image data without numpy/cv2
            width, height = self.capture_width, self.capture_height
            
            # Create a simple gradient pattern
            image_data = []
            for y in range(height):
                row = []
                for x in range(width):
                    # Simple gradient pattern
                    r = int(255 * x / width) if width > 0 else 128
                    g = int(255 * y / height) if height > 0 else 128
                    b = 128
                    row.extend([b, g, r])  # BGR format
                image_data.extend(row)
            
            # Create simple bitmap header for a small image
            # This is a very basic implementation
            if width <= 100 and height <= 100:
                # Create a minimal JPEG-like structure (actually just some bytes)
                fake_jpeg = bytes([
                    0xFF, 0xD8, 0xFF, 0xE0,  # JPEG header
                    0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01,  # JFIF
                ] + [128] * (width * height // 100))  # Some fake image data
            else:
                # For larger images, create more fake data
                fake_jpeg = bytes([0xFF, 0xD8] + [128] * min(1000, width * height // 100) + [0xFF, 0xD9])
            
            # Convert to base64
            image_base64 = base64.b64encode(fake_jpeg).decode('utf-8')
            
            timestamp = datetime.now()
            image_data = {
                'sensor_id': sensor_id,
                'timestamp': timestamp.isoformat(),
                'type': 'image',
                'data': {
                    'format': 'jpeg',
                    'width': width,
                    'height': height,
                    'quality': self.image_quality,
                    'size_bytes': len(fake_jpeg),
                    'image_base64': image_base64,
                    'simulated': True
                },
                'metadata': {
                    'capture_device': 'simulator',
                    'capture_time': timestamp.isoformat(),
                    'location': getattr(self.config, 'location', 'greenhouse_001')
                }
            }
            
            self.total_captures += 1
            self.logger.debug(f"Captured simulated image: {len(fake_jpeg)} bytes")
            
            # Notify callbacks
            self._notify_data(image_data)
            
            return image_data
            
        except Exception as e:
            self.logger.error(f"Error in simulation image capture: {e}")
            raise
    
    async def _capture_simulated_video(self, sensor_id: str, duration: int) -> Dict[str, Any]:
        """Capture simulated video data."""
        try:
            # Create fake video data
            frame_count = int(duration * self.capture_fps)
            
            # Generate minimal MP4-like data
            fake_mp4 = bytes([
                # MP4 file header signature
                0x00, 0x00, 0x00, 0x20, 0x66, 0x74, 0x79, 0x70,
                0x69, 0x73, 0x6F, 0x6D, 0x00, 0x00, 0x02, 0x00,
            ] + [128] * min(2000, frame_count * 10))  # Fake video data
            
            video_base64 = base64.b64encode(fake_mp4).decode('utf-8')
            
            timestamp = datetime.now()
            video_data = {
                'sensor_id': sensor_id,
                'timestamp': timestamp.isoformat(),
                'type': 'video',
                'data': {
                    'format': 'mp4',
                    'width': self.capture_width,
                    'height': self.capture_height,
                    'fps': self.capture_fps,
                    'duration_seconds': duration,
                    'frame_count': frame_count,
                    'size_bytes': len(fake_mp4),
                    'video_base64': video_base64,
                    'simulated': True
                },
                'metadata': {
                    'capture_device': 'simulator',
                    'capture_time': timestamp.isoformat(),
                    'location': getattr(self.config, 'location', 'greenhouse_001')
                }
            }
            
            self.total_captures += 1
            self.logger.debug(f"Captured simulated video: {duration}s, {frame_count} frames, {len(fake_mp4)} bytes")
            
            # Notify callbacks
            self._notify_data(video_data)
            
            return video_data
            
        except Exception as e:
            self.logger.error(f"Error in simulation video capture: {e}")
            raise
    
    async def start_continuous_capture(self, interval: float = 30.0, capture_type: str = "image"):
        """Start continuous capture at specified interval."""
        if not self.is_initialized:
            await self.initialize()
        
        self.logger.info(f"Starting continuous {capture_type} capture every {interval} seconds")
        
        while True:
            try:
                if capture_type == "image":
                    await self.capture_image()
                elif capture_type == "video":
                    await self.capture_video()
                else:
                    self.logger.error(f"Unknown capture type: {capture_type}")
                    break
                
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                self.logger.info("Continuous capture cancelled")
                break
            except Exception as e:
                self.logger.error(f"Error in continuous capture: {e}")
                await asyncio.sleep(5)  # Wait before retry
    
    async def cleanup(self):
        """Clean up camera resources."""
        try:
            if self.camera is not None and CV2_AVAILABLE:
                self.camera.release()
                self.camera = None
            
            self.is_initialized = False
            self.logger.info("Camera adapter cleaned up")
            
        except Exception as e:
            self.logger.error(f"Error during camera cleanup: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get adapter statistics."""
        return {
            'total_captures': self.total_captures,
            'total_errors': self.total_errors,
            'is_initialized': self.is_initialized,
            'simulation_mode': self.simulation_mode,
            'cv2_available': CV2_AVAILABLE,
            'numpy_available': NUMPY_AVAILABLE,
            'camera_settings': {
                'width': self.capture_width,
                'height': self.capture_height,
                'fps': self.capture_fps,
                'quality': self.image_quality
            }
        }
