-- AgriNex 农业物联网数据管理平台
-- 数据库初始化脚本（三层结构：Device-Sensor-Reading）
-- 更新时间: 2025-06-25

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- 1. 用户表 (users)
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '用户ID',
  `username` varchar(80) NOT NULL COMMENT '用户名',
  `password_hash` varchar(255) NOT NULL COMMENT '密码哈希',
  `role` varchar(20) DEFAULT 'user' COMMENT '用户角色: admin/user',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  KEY `idx_role` (`role`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- 2. 设备表 (devices)
DROP TABLE IF EXISTS `devices`;
CREATE TABLE `devices` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '设备ID',
  `name` varchar(255) NOT NULL COMMENT '设备名称',
  `location` varchar(255) COMMENT '设备位置',
  `type` varchar(50) COMMENT '设备类型',
  `status` varchar(50) DEFAULT 'active' COMMENT '设备状态',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_type_status` (`type`, `status`),
  KEY `idx_location` (`location`),
  KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='设备表';

-- 3. 传感器表 (sensors)
DROP TABLE IF EXISTS `sensors`;
CREATE TABLE `sensors` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '传感器ID',
  `device_id` int(11) NOT NULL COMMENT '所属设备ID',
  `type` varchar(50) NOT NULL COMMENT '传感器类型',
  `name` varchar(255) COMMENT '传感器名称',
  `unit` varchar(20) COMMENT '单位',
  `status` varchar(50) DEFAULT 'active' COMMENT '传感器状态',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_device_id` (`device_id`),
  KEY `idx_type` (`type`),
  CONSTRAINT `fk_sensors_device` FOREIGN KEY (`device_id`) REFERENCES `devices` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='传感器表';

-- 4. 读数表 (readings) - 支持多种数据类型
DROP TABLE IF EXISTS `readings`;
CREATE TABLE `readings` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '读数ID',
  `sensor_id` int(11) NOT NULL COMMENT '传感器ID',
  `timestamp` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '时间戳',
  
  -- 数据类型标识
  `data_type` varchar(20) NOT NULL DEFAULT 'numeric' COMMENT '数据类型: numeric/image/video',
  
  -- 数值型数据字段（温度、湿度、光照等）
  `numeric_value` float COMMENT '数值型读数',
  `unit` varchar(10) COMMENT '单位: °C, %, lux等',
  
  -- 文件型数据字段（图片、视频等）
  `file_path` varchar(512) COMMENT '本地文件存储路径（备份）',
  `file_size` bigint COMMENT '文件大小(字节)',
  `file_format` varchar(10) COMMENT '文件格式: jpg, mp4等',
  
  -- 对象存储相关字段
  `storage_backend` varchar(20) DEFAULT 'minio' COMMENT '存储后端: local/minio/dual',
  `bucket_name` varchar(100) COMMENT 'MinIO存储桶名称',
  `object_key` varchar(500) COMMENT '对象存储的key路径',
  `object_url` varchar(1000) COMMENT '对象访问URL',
  `object_etag` varchar(100) COMMENT '对象ETag（用于完整性校验）',
  
  -- 额外元数据
  `meta_info` text COMMENT 'JSON格式的额外信息',
  
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  
  PRIMARY KEY (`id`),
  KEY `idx_sensor_timestamp` (`sensor_id`, `timestamp`),
  KEY `idx_timestamp` (`timestamp`),
  KEY `idx_data_type` (`data_type`),
  KEY `idx_sensor_data_type` (`sensor_id`, `data_type`),
  CONSTRAINT `fk_readings_sensor` FOREIGN KEY (`sensor_id`) REFERENCES `sensors` (`id`) ON DELETE CASCADE,
  
  -- 约束：根据数据类型检查必需字段
  CONSTRAINT `chk_numeric_data` CHECK (
    (data_type = 'numeric' AND numeric_value IS NOT NULL) OR 
    (data_type != 'numeric')
  ),
  CONSTRAINT `chk_file_data` CHECK (
    (data_type IN ('image', 'video') AND file_path IS NOT NULL AND file_format IS NOT NULL) OR 
    (data_type NOT IN ('image', 'video'))
  )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='传感器读数表(支持多种数据类型)';

-- 5. 预测表 (predictions)
DROP TABLE IF EXISTS `predictions`;
CREATE TABLE `predictions` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '预测ID',
  `sensor_id` int(11) NOT NULL COMMENT '传感器ID',
  `predict_ts` datetime NOT NULL COMMENT '预测时间点',
  `yhat` double COMMENT '预测值',
  `yhat_lower` double COMMENT '预测下界',
  `yhat_upper` double COMMENT '预测上界',
  `metric_type` varchar(20) DEFAULT NULL COMMENT '预测指标类型',
  `generated_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '生成时间',
  PRIMARY KEY (`id`),
  KEY `idx_sensor_predict_ts` (`sensor_id`, `predict_ts`),
  KEY `idx_generated_at` (`generated_at`),
  KEY `idx_metric_type` (`metric_type`),
  CONSTRAINT `fk_predictions_sensor` FOREIGN KEY (`sensor_id`) REFERENCES `sensors` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='预测数据表';

-- 6. 告警表 (alarms)
DROP TABLE IF EXISTS `alarms`;
CREATE TABLE `alarms` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '告警ID',
  `sensor_id` int(11) NOT NULL COMMENT '传感器ID',
  `alarm_type` varchar(50) NOT NULL COMMENT '告警类型',
  `threshold_value` float COMMENT '阈值',
  `actual_value` float COMMENT '实际值',
  `severity` varchar(20) DEFAULT 'medium' COMMENT '严重级别',
  `message` text COMMENT '告警消息',
  `status` varchar(20) DEFAULT 'active' COMMENT '告警状态',
  `resolved_at` datetime COMMENT '解决时间',
  `resolved_by` varchar(100) COMMENT '解决人',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_sensor_created` (`sensor_id`, `created_at`),
  KEY `idx_severity_status` (`severity`, `status`),
  KEY `idx_status` (`status`),
  CONSTRAINT `fk_alarms_sensor` FOREIGN KEY (`sensor_id`) REFERENCES `sensors` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='告警表';

-- 7. JWT令牌黑名单表 (token_blacklist)
DROP TABLE IF EXISTS `token_blacklist`;
CREATE TABLE `token_blacklist` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `user_id` int(11) NOT NULL COMMENT '用户ID',
  `jti` varchar(36) NOT NULL COMMENT 'JWT唯一标识符',
  `revoked_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '撤销时间',
  `expires_at` datetime NOT NULL COMMENT '过期时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `jti` (`jti`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_expires_at` (`expires_at`),
  CONSTRAINT `fk_token_blacklist_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='JWT令牌黑名单';

-- 8. 智能建议记录表 (ai_suggestions)
DROP TABLE IF EXISTS `ai_suggestions`;
CREATE TABLE `ai_suggestions` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '建议ID',
  `sensor_id` int(11) COMMENT '关联传感器',
  `user_id` int(11) COMMENT '请求用户',
  `prompt` text COMMENT '输入提示',
  `suggestion` text COMMENT 'AI建议内容',
  `model_used` varchar(50) DEFAULT 'gpt-4o' COMMENT '使用的AI模型',
  `tokens_used` int(11) COMMENT '消耗的token数',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_sensor_created` (`sensor_id`, `created_at`),
  KEY `idx_user_created` (`user_id`, `created_at`),
  CONSTRAINT `fk_ai_suggestions_sensor` FOREIGN KEY (`sensor_id`) REFERENCES `sensors` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_ai_suggestions_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AI智能建议记录表';

SET FOREIGN_KEY_CHECKS = 1;

-- ====================================
-- 触发器 (Triggers)
-- ====================================

-- 1. 设备状态变更时记录日志
DELIMITER $$
CREATE TRIGGER tr_device_status_change 
    AFTER UPDATE ON devices
    FOR EACH ROW
BEGIN
    IF OLD.status != NEW.status THEN
        INSERT INTO device_logs (device_id, old_status, new_status, changed_at, changed_by)
        VALUES (NEW.device_id, OLD.status, NEW.status, NOW(), USER());
    END IF;
END$$
DELIMITER ;

-- 2. 异常读数自动创建告警
DELIMITER $$
CREATE TRIGGER tr_readings_anomaly_detection 
    AFTER INSERT ON readings
    FOR EACH ROW
BEGIN
    DECLARE anomaly_detected BOOLEAN DEFAULT FALSE;
    
    -- 温度异常检测 (超出正常范围 0-50度)
    IF NEW.temperature IS NOT NULL AND (NEW.temperature < 0 OR NEW.temperature > 50) THEN
        SET anomaly_detected = TRUE;
        INSERT INTO alarms (device_id, alarm_type, message, severity, created_at)
        VALUES (NEW.device_id, 'temperature_anomaly', 
                CONCAT('Temperature out of range: ', NEW.temperature, '°C'), 
                'medium', NOW());
    END IF;
    
    -- 湿度异常检测 (超出0-100%)
    IF NEW.humidity IS NOT NULL AND (NEW.humidity < 0 OR NEW.humidity > 100) THEN
        SET anomaly_detected = TRUE;
        INSERT INTO alarms (device_id, alarm_type, message, severity, created_at)
        VALUES (NEW.device_id, 'humidity_anomaly', 
                CONCAT('Humidity out of range: ', NEW.humidity, '%'), 
                'medium', NOW());
    END IF;
    
    -- 光照异常检测 (负值)
    IF NEW.light IS NOT NULL AND NEW.light < 0 THEN
        SET anomaly_detected = TRUE;
        INSERT INTO alarms (device_id, alarm_type, message, severity, created_at)
        VALUES (NEW.device_id, 'light_anomaly', 
                CONCAT('Invalid light reading: ', NEW.light, ' lux'), 
                'low', NOW());
    END IF;
END$$
DELIMITER ;

-- ====================================
-- 视图 (Views)
-- ====================================

-- 1. 设备最新状态视图
CREATE VIEW v_device_latest_status AS
SELECT 
    d.device_id,
    d.name AS device_name,
    d.location,
    d.type,
    d.status,
    r.temperature,
    r.humidity,
    r.light,
    r.timestamp AS last_reading_time,
    CASE 
        WHEN r.timestamp < DATE_SUB(NOW(), INTERVAL 1 HOUR) THEN 'stale'
        WHEN r.timestamp IS NULL THEN 'no_data'
        ELSE 'fresh'
    END AS data_freshness
FROM devices d
LEFT JOIN (
    SELECT device_id, temperature, humidity, light, timestamp,
           ROW_NUMBER() OVER (PARTITION BY device_id ORDER BY timestamp DESC) as rn
    FROM readings
) r ON d.device_id = r.device_id AND r.rn = 1;

-- 2. 设备每日统计视图
CREATE VIEW v_device_daily_stats AS
SELECT 
    device_id,
    DATE(timestamp) AS date,
    COUNT(*) AS reading_count,
    AVG(temperature) AS avg_temp,
    MIN(temperature) AS min_temp,
    MAX(temperature) AS max_temp,
    AVG(humidity) AS avg_humidity,
    MIN(humidity) AS min_humidity,
    MAX(humidity) AS max_humidity,
    AVG(light) AS avg_light,
    MIN(light) AS min_light,
    MAX(light) AS max_light
FROM readings
WHERE timestamp >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
GROUP BY device_id, DATE(timestamp);

-- 3. 活跃告警视图
CREATE VIEW v_active_alarms AS
SELECT 
    a.id,
    a.device_id,
    d.name AS device_name,
    d.location,
    a.alarm_type,
    a.message,
    a.severity,
    a.status,
    a.created_at,
    TIMESTAMPDIFF(MINUTE, a.created_at, NOW()) AS minutes_since_created
FROM alarms a
JOIN devices d ON a.device_id = d.device_id
WHERE a.status = 'active'
ORDER BY 
    FIELD(a.severity, 'critical', 'high', 'medium', 'low'),
    a.created_at DESC;

-- ====================================
-- 存储过程 (Stored Procedures)
-- ====================================

-- 1. 清理旧数据的存储过程
DELIMITER $$
CREATE PROCEDURE sp_cleanup_old_data(IN days_to_keep INT)
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE cleanup_date DATETIME;
    
    SET cleanup_date = DATE_SUB(NOW(), INTERVAL days_to_keep DAY);
    
    START TRANSACTION;
    
    -- 清理旧的读数数据
    DELETE FROM readings WHERE timestamp < cleanup_date;
    
    -- 清理旧的预测数据
    DELETE FROM predictions WHERE generated_at < cleanup_date;
    
    -- 清理已解决的旧告警
    DELETE FROM alarms 
    WHERE status = 'resolved' AND resolved_at < DATE_SUB(NOW(), INTERVAL 7 DAY);
    
    -- 清理过期的token黑名单
    DELETE FROM token_blacklist WHERE expires_at < NOW();
    
    COMMIT;
    
    SELECT CONCAT('Cleanup completed for data older than ', days_to_keep, ' days') AS result;
END$$
DELIMITER ;

-- 2. 设备健康检查存储过程
DELIMITER $$
CREATE PROCEDURE sp_device_health_check()
BEGIN
    -- 检查长时间无数据的设备
    SELECT 
        d.device_id,
        d.name,
        d.location,
        d.status,
        MAX(r.timestamp) AS last_reading,
        TIMESTAMPDIFF(HOUR, MAX(r.timestamp), NOW()) AS hours_since_last_reading
    FROM devices d
    LEFT JOIN readings r ON d.device_id = r.device_id
    WHERE d.status = 'active'
    GROUP BY d.device_id, d.name, d.location, d.status
    HAVING MAX(r.timestamp) < DATE_SUB(NOW(), INTERVAL 2 HOUR) 
        OR MAX(r.timestamp) IS NULL;
END$$
DELIMITER ;

-- 3. 生成设备报告的存储过程
DELIMITER $$
CREATE PROCEDURE sp_generate_device_report(IN device_id_param INT, IN days_back INT)
BEGIN
    DECLARE start_date DATETIME;
    SET start_date = DATE_SUB(NOW(), INTERVAL days_back DAY);
    
    -- 基本设备信息
    SELECT * FROM devices WHERE device_id = device_id_param;
    
    -- 时间段内的统计
    SELECT 
        COUNT(*) AS total_readings,
        AVG(temperature) AS avg_temp,
        MIN(temperature) AS min_temp,
        MAX(temperature) AS max_temp,
        AVG(humidity) AS avg_humidity,
        MIN(humidity) AS min_humidity,
        MAX(humidity) AS max_humidity,
        AVG(light) AS avg_light,
        MIN(light) AS min_light,
        MAX(light) AS max_light
    FROM readings 
    WHERE device_id = device_id_param AND timestamp >= start_date;
    
    -- 告警统计
    SELECT 
        alarm_type,
        COUNT(*) AS alarm_count,
        MAX(created_at) AS latest_alarm
    FROM alarms 
    WHERE device_id = device_id_param AND created_at >= start_date
    GROUP BY alarm_type;
END$$
DELIMITER ;

-- ====================================
-- 数据清理事件 (Events)
-- ====================================

-- 启用事件调度器
SET GLOBAL event_scheduler = ON;

-- 每日清理过期数据事件
DELIMITER $$
CREATE EVENT ev_daily_cleanup
ON SCHEDULE EVERY 1 DAY
STARTS TIMESTAMP(CURRENT_DATE + INTERVAL 1 DAY, '02:00:00')
DO
BEGIN
    -- 清理30天前的数据
    CALL sp_cleanup_old_data(30);
    
    -- 记录清理日志
    INSERT INTO system_logs (log_type, message, created_at)
    VALUES ('cleanup', 'Daily data cleanup completed', NOW());
END$$
DELIMITER ;

-- 创建数据库用户（可选）
-- CREATE USER 'agri_user'@'%' IDENTIFIED BY 'agri_password';
-- GRANT ALL PRIVILEGES ON agri_iot.* TO 'agri_user'@'%';
-- FLUSH PRIVILEGES;
