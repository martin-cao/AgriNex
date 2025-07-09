from datetime import datetime
import json
import logging
import os

try:
    import redis
    RedisError = redis.RedisError
except ImportError:
    # Redis 模块未安装时的处理
    redis = None
    RedisError = Exception

from utils.redis_client import redis_client

# 配置日志
logger = logging.getLogger(__name__)

class TokenBlacklistService:
    """
    基于Redis的JWT Token黑名单服务
    
    Redis key格式: blacklist:token:{jti}
    Value: {"user_id": 123, "revoked_at": "2025-06-25T10:30:00", "expires_at": "..."}
    
    Features:
    - 自动TTL管理：token过期后自动从Redis删除
    - 降级处理：Redis不可用时使用内存临时存储
    - 批量操作：支持撤销用户的所有token
    - 详细日志：便于调试和监控
    """
    
    def __init__(self, redis_client_instance=None):
        self.redis_client = redis_client_instance or redis_client
        self.prefix = "blacklist:token:"
    
    def revoke_token(self, jti, user_id, expires_at):
        """撤销token"""
        if not self.redis_client or not self.redis_client.client:
            # Redis不可用时的降级处理
            logger.warning("Redis unavailable, using fallback for jti: %s", jti)
            return self._fallback_revoke(jti)
        
        try:
            key = f"{self.prefix}{jti}"
            value = {
                "user_id": user_id,
                "revoked_at": datetime.utcnow().isoformat(),
                "expires_at": expires_at.isoformat() if isinstance(expires_at, datetime) else str(expires_at)
            }
            
            # 计算TTL（到token过期的秒数）
            if isinstance(expires_at, datetime):
                ttl = int((expires_at - datetime.utcnow()).total_seconds())
            else:
                # 假设expires_at是时间戳
                ttl = int(expires_at - datetime.utcnow().timestamp())
                
            if ttl > 0:
                success = self.redis_client.set(key, json.dumps(value), ex=ttl)
                if success:
                    logger.info("Token revoked successfully: jti=%s, user_id=%s", jti, user_id)
                    return True
                else:
                    logger.error("Failed to revoke token: jti=%s", jti)
                    return self._fallback_revoke(jti)
            else:
                logger.warning("Token already expired: jti=%s", jti)
                return False
            
        except (RedisError, ValueError, TypeError) as e:
            logger.error("Redis revoke failed for jti=%s: %s", jti, e)
            return self._fallback_revoke(jti)
    
    def is_token_revoked(self, jti):
        """检查token是否被撤销"""
        if not self.redis_client or not self.redis_client.client:
            # Redis不可用时的降级处理
            return self._fallback_check(jti)
        
        try:
            key = f"{self.prefix}{jti}"
            exists = self.redis_client.exists(key)
            logger.debug("Token revocation check: jti=%s, revoked=%s", jti, bool(exists))
            return bool(exists)
        except (RedisError, TypeError) as e:
            logger.error("Redis check failed for jti=%s: %s", jti, e)
            return self._fallback_check(jti)
    
    def get_revoked_info(self, jti):
        """获取撤销信息"""
        if not self.redis_client or not self.redis_client.client:
            return None
        
        try:
            key = f"{self.prefix}{jti}"
            data = self.redis_client.get(key)
            return json.loads(data) if data else None
        except (RedisError, ValueError, TypeError):
            return None
    
    def revoke_all_user_tokens(self, user_id):
        """撤销某用户的所有token（通过模式匹配）"""
        if not self.redis_client or not self.redis_client.client:
            logger.warning("Redis unavailable, cannot revoke all tokens for user: %s", user_id)
            return 0
        
        try:
            # 注意：scan比keys更安全，不会阻塞Redis
            pattern = f"{self.prefix}*"
            revoked_count = 0
            
            for key in self.redis_client.client.scan_iter(match=pattern):
                try:
                    data = self.redis_client.get(key)
                    if data:
                        token_info = json.loads(data)
                        if token_info.get("user_id") == user_id:
                            # 保持原有TTL，只更新撤销时间
                            token_info["revoked_at"] = datetime.utcnow().isoformat()
                            ttl = self.redis_client.client.ttl(key)
                            if ttl > 0:
                                self.redis_client.set(key.split(':')[-1], json.dumps(token_info), ex=ttl)
                                revoked_count += 1
                except (ValueError, TypeError) as e:
                    logger.warning("Error processing token data for key %s: %s", key, e)
                    continue
            
            logger.info("Revoked %d tokens for user: %s", revoked_count, user_id)
            return revoked_count
            
        except RedisError as e:
            logger.error("Redis error revoking all tokens for user %s: %s", user_id, e)
            return 0
    
    def clear_expired_tokens(self):
        """清理过期token（Redis自动TTL，这个方法主要用于统计）"""
        # Redis会自动删除过期的key，这里可以做一些统计工作
        if not self.redis_client or not self.redis_client.client:
            return 0
        
        try:
            pattern = f"{self.prefix}*"
            active_count = 0
            for _ in self.redis_client.client.scan_iter(match=pattern):
                active_count += 1
            
            logger.info("Active blacklisted tokens count: %d", active_count)
            return active_count
        except RedisError as e:
            logger.error("Error counting active tokens: %s", e)
            return 0
    
    # 多级降级处理（Redis不可用时）
    _memory_fallback = set()  # 最后的内存存储
    
    def _fallback_revoke(self, jti):
        """多级降级撤销策略"""
        # 1. 尝试MySQL降级
        if self._mysql_fallback_revoke(jti):
            return True
            
        # 2. 尝试文件降级
        if self._file_fallback_revoke(jti):
            return True
            
        # 3. 最后使用内存降级
        return self._memory_fallback_revoke(jti)
    
    def _fallback_check(self, jti):
        """多级降级检查策略"""
        # 按优先级检查各个降级存储
        return (self._mysql_fallback_check(jti) or 
                self._file_fallback_check(jti) or 
                self._memory_fallback_check(jti))
    
    def _mysql_fallback_revoke(self, jti):
        """MySQL降级撤销"""
        try:
            # 动态导入，避免循环依赖
            from extensions import db
            from sqlalchemy import text
            
            # 使用简单的临时表
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS token_blacklist_fallback (
                    jti VARCHAR(36) PRIMARY KEY,
                    revoked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NULL,
                    INDEX idx_expires (expires_at)
                )
            """))
            
            # 插入或更新撤销记录
            db.session.execute(text("""
                INSERT INTO token_blacklist_fallback (jti, revoked_at) 
                VALUES (:jti, :revoked_at)
                ON DUPLICATE KEY UPDATE revoked_at = :revoked_at
            """), {
                'jti': jti,
                'revoked_at': datetime.utcnow()
            })
            
            db.session.commit()
            logger.info("MySQL fallback revoke success: jti=%s", jti)
            return True
            
        except Exception as e:
            logger.warning("MySQL fallback revoke failed: %s", e)
            return False
    
    def _mysql_fallback_check(self, jti):
        """MySQL降级检查"""
        try:
            from extensions import db
            from sqlalchemy import text
            
            result = db.session.execute(text("""
                SELECT 1 FROM token_blacklist_fallback 
                WHERE jti = :jti 
                AND (expires_at IS NULL OR expires_at > NOW())
                LIMIT 1
            """), {'jti': jti})
            
            exists = result.fetchone() is not None
            logger.debug("MySQL fallback check: jti=%s, revoked=%s", jti, exists)
            return exists
            
        except Exception as e:
            logger.warning("MySQL fallback check failed: %s", e)
            return False
    
    def _file_fallback_revoke(self, jti):
        """文件降级撤销"""
        try:
            import os
            fallback_file = "/tmp/agrinex_token_blacklist.txt"
            
            # 检查文件大小，避免无限增长
            if os.path.exists(fallback_file) and os.path.getsize(fallback_file) > 10 * 1024 * 1024:  # 10MB
                self._cleanup_fallback_file(fallback_file)
            
            with open(fallback_file, 'a') as f:
                try:
                    import fcntl
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX)  # 文件锁
                except ImportError:
                    pass  # Windows上没有fcntl
                
                f.write(f"{jti}|{datetime.utcnow().isoformat()}\n")
                f.flush()
                os.fsync(f.fileno())  # 强制写入磁盘
            
            logger.info("File fallback revoke success: jti=%s", jti)
            return True
            
        except Exception as e:
            logger.warning("File fallback revoke failed: %s", e)
            return False
    
    def _file_fallback_check(self, jti):
        """文件降级检查"""
        try:
            fallback_file = "/tmp/agrinex_token_blacklist.txt"
            
            if not os.path.exists(fallback_file):
                return False
            
            # 读取文件检查token
            with open(fallback_file, 'r') as f:
                for line in f:
                    if line.startswith(f"{jti}|"):
                        # 可以添加过期时间检查
                        logger.debug("File fallback check: jti=%s, revoked=True", jti)
                        return True
            
            return False
            
        except Exception as e:
            logger.warning("File fallback check failed: %s", e)
            return False
    
    def _cleanup_fallback_file(self, fallback_file):
        """清理降级文件，移除过期记录"""
        try:
            import tempfile
            temp_file = tempfile.mktemp()
            current_time = datetime.utcnow()
            
            with open(fallback_file, 'r') as infile, open(temp_file, 'w') as outfile:
                for line in infile:
                    parts = line.strip().split('|')
                    if len(parts) >= 2:
                        try:
                            revoked_time = datetime.fromisoformat(parts[1])
                            # 保留最近24小时的记录
                            if (current_time - revoked_time).total_seconds() < 24 * 3600:
                                outfile.write(line)
                        except ValueError:
                            continue
            
            os.replace(temp_file, fallback_file)
            logger.info("Cleaned up fallback file")
            
        except Exception as e:
            logger.error("Error cleaning fallback file: %s", e)
    
    def _memory_fallback_revoke(self, jti):
        """内存降级撤销（最后手段）"""
        self._memory_fallback.add(jti)
        logger.warning("Using memory fallback for token revocation: jti=%s", jti)
        
        # 限制内存使用，避免内存泄漏
        if len(self._memory_fallback) > 10000:  # 最多1万个token
            # 移除一半最旧的token（简单的LRU策略）
            to_remove = list(self._memory_fallback)[:5000]
            for token in to_remove:
                self._memory_fallback.discard(token)
            logger.warning("Memory fallback size limit reached, cleaned up old tokens")
        
        return True
    
    def _memory_fallback_check(self, jti):
        """内存降级检查（最后手段）"""
        is_revoked = jti in self._memory_fallback
        logger.debug("Memory fallback check: jti=%s, revoked=%s", jti, is_revoked)
        return is_revoked
    
    def get_stats(self):
        """获取token黑名单统计信息"""
        stats = {
            "redis_available": bool(self.redis_client and self.redis_client.client),
            "fallback_tokens_count": len(self._memory_fallback),
            "active_blacklisted_count": 0
        }
        
        if stats["redis_available"] and self.redis_client.client:
            try:
                pattern = f"{self.prefix}*"
                # 使用client.scan_iter，确保client存在
                if hasattr(self.redis_client.client, 'scan_iter'):
                    stats["active_blacklisted_count"] = sum(1 for _ in self.redis_client.client.scan_iter(match=pattern))
                elif hasattr(self.redis_client.client, 'keys'):
                    # 降级为使用keys（虽然不推荐在生产环境）
                    keys = self.redis_client.client.keys(pattern)
                    stats["active_blacklisted_count"] = len(keys)
            except RedisError as e:
                logger.error("Error getting stats: %s", e)
        
        return stats


# 全局实例
token_blacklist_service = TokenBlacklistService()


# 兼容性接口 - 为了保持与现有代码的兼容性
class TokenBlacklist:
    """兼容性接口，实际使用Redis服务"""
    
    @classmethod
    def is_token_revoked(cls, jti):
        """检查token是否被撤销"""
        return token_blacklist_service.is_token_revoked(jti)
    
    @classmethod
    def revoke_token(cls, jti, user_id, expires_at):
        """撤销token"""
        return token_blacklist_service.revoke_token(jti, user_id, expires_at)
    
    @classmethod
    def get_revoked_info(cls, jti):
        """获取撤销信息"""
        return token_blacklist_service.get_revoked_info(jti)
    
    @classmethod
    def revoke_all_user_tokens(cls, user_id):
        """撤销某用户的所有token"""
        return token_blacklist_service.revoke_all_user_tokens(user_id)
