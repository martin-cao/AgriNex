# backend/services/storage_service.py
import os
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Optional, BinaryIO, Dict, Any, Union
import logging

try:
    from minio import Minio
    from minio.error import S3Error
    MINIO_AVAILABLE = True
except ImportError:
    MINIO_AVAILABLE = False
    Minio = None
    S3Error = Exception
    logging.warning("MinIO not available, using local storage only")

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None
    logging.warning("PIL not available, thumbnail generation disabled")

class StorageService:
    """
    统一存储服务，支持MinIO对象存储和本地文件系统备份
    """
    
    def __init__(self):
        self.minio_client = None
        self.local_storage_path = './storage'
        self._initialize_storage()
    
    def _initialize_storage(self):
        """初始化存储服务"""
        try:
            # 初始化本地存储路径
            self.local_storage_path = os.getenv('LOCAL_STORAGE_PATH', './storage')
            os.makedirs(self.local_storage_path, exist_ok=True)
            
            # 初始化MinIO客户端
            if MINIO_AVAILABLE:
                minio_endpoint = os.getenv('MINIO_ENDPOINT', 'localhost:9000')
                minio_access_key = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
                minio_secret_key = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
                minio_secure = os.getenv('MINIO_SECURE', 'False').lower() == 'true'
                
                self.minio_client = Minio(
                    endpoint=minio_endpoint,
                    access_key=minio_access_key,
                    secret_key=minio_secret_key,
                    secure=minio_secure
                )
                logging.info("MinIO client initialized successfully")
            
            logging.info("Storage service initialized successfully")
            
        except Exception as e:
            logging.error(f"Failed to initialize storage service: {e}")
            # 仍然可以使用本地存储
    
    def ensure_bucket_exists(self, bucket_name: str) -> bool:
        """确保bucket存在，不存在则创建"""
        if not self.minio_client:
            return True  # 如果没有MinIO，总是返回True
            
        try:
            if not self.minio_client.bucket_exists(bucket_name):
                self.minio_client.make_bucket(bucket_name)
                logging.info(f"Created bucket: {bucket_name}")
            return True
        except Exception as e:
            logging.error(f"Failed to ensure bucket {bucket_name}: {e}")
            return False
    
    def upload_file(self, 
                   file_data: BinaryIO, 
                   bucket_name: str,
                   data_type: str,
                   device_id: str,
                   sensor_id: str,
                   file_format: Optional[str] = None,
                   metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        上传文件到MinIO和本地存储
        """
        try:
            # 生成对象键
            object_key = self._generate_object_key(data_type, device_id, sensor_id, file_format)
            
            # 准备元数据
            object_metadata = {
                'device_id': device_id,
                'sensor_id': sensor_id,
                'data_type': data_type,
                'upload_time': datetime.utcnow().isoformat(),
                'file_format': file_format or 'unknown'
            }
            if metadata:
                object_metadata.update(metadata)
            
            # 获取文件大小
            file_data.seek(0, 2)  # 移到文件末尾
            file_size = file_data.tell()
            file_data.seek(0)  # 重置到开头
            
            # 保存到本地文件系统
            local_path = self._save_to_local(file_data, object_key)
            
            # 默认结果
            result = {
                'success': True,
                'storage_backend': 'local',
                'bucket_name': bucket_name,
                'object_key': object_key,
                'object_url': None,
                'object_etag': None,
                'file_path': local_path,
                'file_size': file_size,
                'file_format': file_format,
                'metadata': object_metadata,
                'thumbnail_info': None
            }
            
            # 尝试上传到MinIO
            if self.minio_client:
                try:
                    # 确保bucket存在
                    self.ensure_bucket_exists(bucket_name)
                    
                    # 上传到MinIO
                    minio_result = self.minio_client.put_object(
                        bucket_name=bucket_name,
                        object_name=object_key,
                        data=file_data,
                        length=file_size,
                        metadata=object_metadata
                    )
                    
                    # 更新结果
                    result.update({
                        'storage_backend': 'minio',
                        'object_url': self._generate_object_url(bucket_name, object_key),
                        'object_etag': minio_result.etag
                    })
                    
                except Exception as e:
                    logging.error(f"Failed to upload to MinIO: {e}")
                    # 继续使用本地存储
            
            # 如果是图片，生成缩略图
            if data_type == 'image' and PIL_AVAILABLE:
                thumbnail_info = self._generate_thumbnail(file_data, bucket_name, object_key)
                result['thumbnail_info'] = thumbnail_info
            
            return result
            
        except Exception as e:
            logging.error(f"Failed to upload file: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def download_file(self, bucket_name: str, object_key: str) -> Optional[BinaryIO]:
        """从MinIO下载文件，失败时尝试本地文件"""
        # 首先尝试从MinIO下载
        if self.minio_client:
            try:
                response = self.minio_client.get_object(bucket_name, object_key)
                return response
            except Exception as e:
                logging.error(f"Failed to download from MinIO: {e}")
        
        # 尝试从本地文件系统读取
        try:
            local_path = os.path.join(self.local_storage_path, object_key)
            if os.path.exists(local_path):
                return open(local_path, 'rb')
        except Exception as e:
            logging.error(f"Failed to read local file: {e}")
        
        return None
    
    def delete_file(self, bucket_name: str, object_key: str, local_path: Optional[str] = None) -> bool:
        """删除MinIO和本地文件"""
        success = True
        
        # 删除MinIO对象
        if self.minio_client:
            try:
                self.minio_client.remove_object(bucket_name, object_key)
            except Exception as e:
                logging.error(f"Failed to delete from MinIO: {e}")
                success = False
        
        # 删除本地文件
        try:
            if local_path and os.path.exists(local_path):
                os.remove(local_path)
            else:
                # 尝试根据object_key找到本地文件
                default_local_path = os.path.join(self.local_storage_path, object_key)
                if os.path.exists(default_local_path):
                    os.remove(default_local_path)
        except Exception as e:
            logging.error(f"Failed to delete local file: {e}")
            success = False
        
        return success
    
    def get_file_metadata(self, bucket_name: str, object_key: str) -> Optional[Dict[str, Any]]:
        """获取文件元数据"""
        if self.minio_client:
            try:
                stat = self.minio_client.stat_object(bucket_name, object_key)
                return {
                    'size': stat.size,
                    'etag': stat.etag,
                    'last_modified': stat.last_modified,
                    'metadata': stat.metadata,
                    'content_type': stat.content_type
                }
            except Exception as e:
                logging.error(f"Failed to get metadata from MinIO: {e}")
        
        # 尝试从本地文件系统获取
        try:
            local_path = os.path.join(self.local_storage_path, object_key)
            if os.path.exists(local_path):
                stat = os.stat(local_path)
                return {
                    'size': stat.st_size,
                    'last_modified': datetime.fromtimestamp(stat.st_mtime),
                    'metadata': {},
                    'content_type': None
                }
        except Exception as e:
            logging.error(f"Failed to get local file metadata: {e}")
        
        return None
    
    def generate_presigned_url(self, bucket_name: str, object_key: str, expires: timedelta = timedelta(hours=1)) -> Optional[str]:
        """生成预签名URL用于临时访问"""
        if not self.minio_client:
            return None
            
        try:
            url = self.minio_client.presigned_get_object(bucket_name, object_key, expires=expires)
            return url
        except Exception as e:
            logging.error(f"Failed to generate presigned URL for {object_key}: {e}")
            return None
    
    def _generate_object_key(self, data_type: str, device_id: str, sensor_id: str, file_format: Optional[str] = None) -> str:
        """生成对象键"""
        timestamp = datetime.utcnow().strftime('%Y/%m/%d/%H')
        uuid_str = str(uuid.uuid4())[:8]
        
        if file_format:
            filename = f"{device_id}_{sensor_id}_{uuid_str}.{file_format}"
        else:
            filename = f"{device_id}_{sensor_id}_{uuid_str}"
        
        return f"{data_type}/{timestamp}/{filename}"
    
    def _generate_object_url(self, bucket_name: str, object_key: str) -> str:
        """生成对象访问URL"""
        endpoint = os.getenv('MINIO_ENDPOINT', 'localhost:9000')
        secure = os.getenv('MINIO_SECURE', 'False').lower() == 'true'
        protocol = 'https' if secure else 'http'
        return f"{protocol}://{endpoint}/{bucket_name}/{object_key}"
    
    def _save_to_local(self, file_data: BinaryIO, object_key: str) -> str:
        """保存文件到本地文件系统"""
        file_data.seek(0)
        local_path = os.path.join(self.local_storage_path, object_key)
        
        # 确保目录存在
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        with open(local_path, 'wb') as f:
            f.write(file_data.read())
        
        file_data.seek(0)  # 重置文件指针
        return local_path
    
    def _generate_thumbnail(self, file_data: BinaryIO, bucket_name: str, object_key: str) -> Optional[Dict[str, Any]]:
        """为图片生成缩略图"""
        if not PIL_AVAILABLE:
            return None
            
        try:
            file_data.seek(0)
            with Image.open(file_data) as img:
                # 生成缩略图
                img.thumbnail((300, 300), Image.Resampling.LANCZOS)
                
                # 保存缩略图到内存
                from io import BytesIO
                thumbnail_buffer = BytesIO()
                img_format = img.format or 'JPEG'
                img.save(thumbnail_buffer, format=img_format)
                thumbnail_size = thumbnail_buffer.tell()
                thumbnail_buffer.seek(0)
                
                # 生成缩略图对象键
                thumbnail_key = object_key.replace('.', '_thumb.')
                
                # 保存缩略图到本地
                thumbnail_local_path = self._save_to_local(thumbnail_buffer, thumbnail_key)
                
                result = {
                    'thumbnail_key': thumbnail_key,
                    'thumbnail_path': thumbnail_local_path,
                    'thumbnail_size': thumbnail_size
                }
                
                # 尝试上传缩略图到MinIO
                if self.minio_client:
                    try:
                        self.minio_client.put_object(
                            bucket_name=bucket_name,
                            object_name=thumbnail_key,
                            data=thumbnail_buffer,
                            length=thumbnail_size,
                            content_type=f'image/{img_format.lower()}'
                        )
                        result['thumbnail_url'] = self._generate_object_url(bucket_name, thumbnail_key)
                    except Exception as e:
                        logging.error(f"Failed to upload thumbnail to MinIO: {e}")
                
                return result
                
        except Exception as e:
            logging.error(f"Failed to generate thumbnail for {object_key}: {e}")
            return None
        finally:
            file_data.seek(0)
    
    def list_objects(self, bucket_name: str, prefix: Optional[str] = None, limit: int = 100) -> list:
        """列出对象"""
        if not self.minio_client:
            return []
            
        try:
            objects = self.minio_client.list_objects(
                bucket_name, 
                prefix=prefix, 
                recursive=True
            )
            
            result = []
            count = 0
            for obj in objects:
                if count >= limit:
                    break
                result.append({
                    'object_name': obj.object_name,
                    'size': obj.size,
                    'etag': obj.etag,
                    'last_modified': obj.last_modified,
                    'is_dir': obj.is_dir
                })
                count += 1
            
            return result
            
        except Exception as e:
            logging.error(f"Failed to list objects in {bucket_name}: {e}")
            return []

# 创建全局存储服务实例
storage_service = StorageService()
