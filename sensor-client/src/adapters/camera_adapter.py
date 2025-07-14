"""
Camera adapter for capturing images and videos from device camera.
支持从设备摄像头捕获图片和视频。
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
    print("Warning: OpenCV not available. Camera functionality will be limited to simulation mode.")

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
        
        # Operating mode
        self.simulation_mode = getattr(config, 'simulation_mode', False)
        
        # Camera object
        self.camera: Optional[cv2.VideoCapture] = None
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
            
            # Initialize camera
            self.camera = cv2.VideoCapture(self.camera_index)
            
            if not self.camera.isOpened():
                raise Exception(f"Cannot open camera {self.camera_index}")
            
            # Set camera properties
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.capture_width)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.capture_height)
            self.camera.set(cv2.CAP_PROP_FPS, self.capture_fps)
            
            # Test capture
            ret, frame = self.camera.read()
            if not ret:
                raise Exception("Cannot capture test frame")
            
            self.logger.info(f"Camera initialized: {self.capture_width}x{self.capture_height} @ {self.capture_fps}fps")
            self.is_initialized = True
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize camera: {e}")
            self._notify_error("camera_initialization", e)
            return False
    
    async def capture_image(self, sensor_id: str = "camera_001") -> Optional[Dict[str, Any]]:
        """Capture a single image."""
        try:
            if self.simulation_mode:
                return await self._capture_simulated_image(sensor_id)
            
            if not self.is_initialized or self.camera is None:
                raise Exception("Camera not initialized")
            
            # Capture frame
            ret, frame = self.camera.read()
            if not ret:
                raise Exception("Failed to capture frame")
            
            # Encode image to JPEG
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
            self.logger.debug(f"Captured image: {len(buffer)} bytes")
            
            # Notify callbacks
            self._notify_data(image_data)
            
            return image_data
            
        except Exception as e:
            self.total_errors += 1
            self.logger.error(f"Error capturing image: {e}")
            self._notify_error("image_capture", e)
            return None
    
    async def capture_video(self, duration: Optional[int] = None, sensor_id: str = "camera_001") -> Optional[Dict[str, Any]]:
        """Capture a video for specified duration."""
        try:
            # Ensure duration is set
            capture_duration = duration if duration is not None else self.video_duration
            
            if self.simulation_mode:
                return await self._capture_simulated_video(sensor_id, capture_duration)
            
            if not self.is_initialized or self.camera is None:
                raise Exception("Camera not initialized")
            
            # Use the determined duration
            final_duration = capture_duration
            
            # Create temporary file for video
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
                temp_path = temp_file.name
            
            try:
                # Initialize video writer
                fourcc = cv2.VideoWriter.fourcc(*self.video_codec)
                writer = cv2.VideoWriter(
                    temp_path,
                    fourcc,
                    self.capture_fps,
                    (self.capture_width, self.capture_height)
                )
                
                if not writer.isOpened():
                    raise Exception("Failed to initialize video writer")
                
                # Record video
                start_time = datetime.now()
                frame_count = 0
                
                self.logger.info(f"Recording video for {final_duration} seconds...")
                
                while (datetime.now() - start_time).total_seconds() < final_duration:
                    ret, frame = self.camera.read()
                    if not ret:
                        self.logger.warning("Failed to read frame during video capture")
                        continue
                    
                    writer.write(frame)
                    frame_count += 1
                    
                    # Small delay to control frame rate
                    await asyncio.sleep(1.0 / self.capture_fps)
                
                writer.release()
                
                # Read video file and encode to base64
                with open(temp_path, 'rb') as f:
                    video_bytes = f.read()
                
                video_base64 = base64.b64encode(video_bytes).decode('utf-8')
                
                # Create data structure
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
                        'duration_seconds': final_duration,
                        'frame_count': frame_count,
                        'size_bytes': len(video_bytes),
                        'video_base64': video_base64
                    },
                    'metadata': {
                        'capture_device': f"camera_{self.camera_index}",
                        'capture_time': timestamp.isoformat(),
                        'location': getattr(self.config, 'location', 'greenhouse_001')
                    }
                }
                
                self.total_captures += 1
                self.logger.info(f"Captured video: {final_duration}s, {frame_count} frames, {len(video_bytes)} bytes")
                
                # Notify callbacks
                self._notify_data(video_data)
                
                return video_data
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_path)
                except:
                    pass
            
        except Exception as e:
            self.total_errors += 1
            self.logger.error(f"Error capturing video: {e}")
            self._notify_error("video_capture", e)
            return None
    
    async def _capture_simulated_image(self, sensor_id: str) -> Dict[str, Any]:
        """Capture simulated image data."""
        import numpy as np
        
        # Generate random colored image
        height, width = self.capture_height, self.capture_width
        
        # Create a gradient background with some random noise
        image = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Add gradient
        for y in range(height):
            for x in range(width):
                image[y, x] = [
                    int(255 * x / width),  # Red gradient
                    int(255 * y / height),  # Green gradient
                    128  # Blue constant
                ]
        
        # Add some random noise
        noise = np.random.randint(0, 50, (height, width, 3), dtype=np.uint8)
        image = cv2.add(image, noise)
        
        # Add timestamp text
        timestamp = datetime.now()
        text = f"SIM {timestamp.strftime('%H:%M:%S')}"
        cv2.putText(image, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # Encode to JPEG
        encode_params = [cv2.IMWRITE_JPEG_QUALITY, self.image_quality]
        success, buffer = cv2.imencode('.jpg', image, encode_params)
        
        if not success:
            raise Exception("Failed to encode simulated image")
        
        image_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return {
            'sensor_id': sensor_id,
            'timestamp': timestamp.isoformat(),
            'type': 'image',
            'data': {
                'format': 'jpeg',
                'width': width,
                'height': height,
                'quality': self.image_quality,
                'size_bytes': len(buffer),
                'image_base64': image_base64,
                'simulated': True
            },
            'metadata': {
                'capture_device': 'simulator',
                'capture_time': timestamp.isoformat(),
                'location': getattr(self.config, 'location', 'greenhouse_001')
            }
        }
    
    async def _capture_simulated_video(self, sensor_id: str, duration: int) -> Dict[str, Any]:
        """Capture simulated video data."""
        import numpy as np
        
        # Create temporary file for simulated video
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Initialize video writer
            fourcc = cv2.VideoWriter.fourcc(*self.video_codec)
            writer = cv2.VideoWriter(
                temp_path,
                fourcc,
                self.capture_fps,
                (self.capture_width, self.capture_height)
            )
            
            # Generate frames
            frame_count = int(duration * self.capture_fps)
            
            for frame_idx in range(frame_count):
                # Create animated frame
                image = np.zeros((self.capture_height, self.capture_width, 3), dtype=np.uint8)
                
                # Animated circle
                center_x = int(self.capture_width // 2 + 100 * np.sin(frame_idx * 0.1))
                center_y = int(self.capture_height // 2 + 50 * np.cos(frame_idx * 0.1))
                radius = int(30 + 20 * np.sin(frame_idx * 0.2))
                color = (
                    int(128 + 127 * np.sin(frame_idx * 0.05)),
                    int(128 + 127 * np.cos(frame_idx * 0.05)),
                    200
                )
                
                cv2.circle(image, (center_x, center_y), radius, color, -1)
                
                # Add frame counter
                text = f"SIM Frame {frame_idx + 1}/{frame_count}"
                cv2.putText(image, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                writer.write(image)
            
            writer.release()
            
            # Read video file
            with open(temp_path, 'rb') as f:
                video_bytes = f.read()
            
            video_base64 = base64.b64encode(video_bytes).decode('utf-8')
            
            timestamp = datetime.now()
            return {
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
                    'size_bytes': len(video_bytes),
                    'video_base64': video_base64,
                    'simulated': True
                },
                'metadata': {
                    'capture_device': 'simulator',
                    'capture_time': timestamp.isoformat(),
                    'location': getattr(self.config, 'location', 'greenhouse_001')
                }
            }
            
        finally:
            # Clean up
            try:
                os.unlink(temp_path)
            except:
                pass
    
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
            if self.camera is not None:
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
            'camera_settings': {
                'width': self.capture_width,
                'height': self.capture_height,
                'fps': self.capture_fps,
                'quality': self.image_quality
            }
        }
