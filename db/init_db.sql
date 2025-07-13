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
  `ip_address` varchar(45) COMMENT '设备IP地址',
  `port` int(11) COMMENT '设备端口',
  `is_active` tinyint(1) DEFAULT 1 COMMENT '是否启用',
  `client_id` varchar(255) COMMENT 'MQTT客户端ID',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_client_id` (`client_id`),
  KEY `idx_type_status` (`type`, `status`),
  KEY `idx_location` (`location`),
  KEY `idx_status` (`status`),
  KEY `idx_is_active` (`is_active`)
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

-- 7. 告警规则表 (alarm_rules)
DROP TABLE IF EXISTS `alarm_rules`;
CREATE TABLE `alarm_rules` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '规则ID',
  `name` varchar(100) NOT NULL COMMENT '规则名称',
  `description` text COMMENT '规则描述',
  `sensor_id` int(11) NOT NULL COMMENT '传感器ID',
  `rule_type` varchar(50) NOT NULL COMMENT '规则类型: threshold/change_rate/pattern',
  `condition` varchar(20) NOT NULL COMMENT '条件操作符: >, <, >=, <=, ==, !=',
  `threshold_value` float NOT NULL COMMENT '阈值',
  `consecutive_count` int(11) DEFAULT 1 COMMENT '连续触发次数',
  `is_active` tinyint(1) DEFAULT 1 COMMENT '是否启用',
  `severity` varchar(20) DEFAULT 'medium' COMMENT '严重级别: low/medium/high',
  `email_enabled` tinyint(1) DEFAULT 0 COMMENT '是否启用邮件通知',
  `webhook_enabled` tinyint(1) DEFAULT 0 COMMENT '是否启用Webhook通知',
  `webhook_url` varchar(500) COMMENT 'Webhook URL',
  `created_by` varchar(100) NOT NULL COMMENT '创建者',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_sensor_active` (`sensor_id`, `is_active`),
  KEY `idx_rule_type` (`rule_type`),
  KEY `idx_severity` (`severity`),
  CONSTRAINT `fk_alarm_rules_sensor` FOREIGN KEY (`sensor_id`) REFERENCES `sensors` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='告警规则表';

-- 8. 告警状态表 (alarm_states)
DROP TABLE IF EXISTS `alarm_states`;
CREATE TABLE `alarm_states` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '状态ID',
  `alarm_rule_id` int(11) NOT NULL COMMENT '告警规则ID',
  `consecutive_count` int(11) DEFAULT 0 COMMENT '连续触发计数',
  `last_triggered_at` datetime COMMENT '最后触发时间',
  `last_value` float COMMENT '最后触发值',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_alarm_rule` (`alarm_rule_id`),
  KEY `idx_last_triggered` (`last_triggered_at`),
  CONSTRAINT `fk_alarm_states_rule` FOREIGN KEY (`alarm_rule_id`) REFERENCES `alarm_rules` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='告警状态跟踪表';

-- 9. JWT令牌黑名单表 (token_blacklist)
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

-- 10. 设备日志表 (device_logs)
DROP TABLE IF EXISTS `device_logs`;
CREATE TABLE `device_logs` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '日志ID',
  `device_id` int(11) NOT NULL COMMENT '设备ID',
  `old_status` varchar(50) COMMENT '旧状态',
  `new_status` varchar(50) COMMENT '新状态',
  `changed_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '变更时间',
  `changed_by` varchar(100) COMMENT '变更人',
  PRIMARY KEY (`id`),
  KEY `idx_device_changed` (`device_id`, `changed_at`),
  CONSTRAINT `fk_device_logs_device` FOREIGN KEY (`device_id`) REFERENCES `devices` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='设备状态变更日志';

-- 11. 系统日志表 (system_logs)
DROP TABLE IF EXISTS `system_logs`;
CREATE TABLE `system_logs` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '日志ID',
  `log_type` varchar(50) NOT NULL COMMENT '日志类型',
  `message` text COMMENT '日志消息',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_type_created` (`log_type`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统日志表';

-- 12. 智能建议记录表 (ai_suggestions)
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

-- 13. 设备模板表 (device_templates)
DROP TABLE IF EXISTS `device_templates`;
CREATE TABLE `device_templates` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '模板ID',
  `device_type` varchar(50) NOT NULL UNIQUE COMMENT '设备类型',
  `name` varchar(255) NOT NULL COMMENT '模板名称',
  `description` text COMMENT '模板描述',
  `manufacturer` varchar(255) COMMENT '制造商',
  `model` varchar(255) COMMENT '型号',
  `sensor_configs` json NOT NULL COMMENT '传感器配置JSON',
  `default_config` json DEFAULT NULL COMMENT '默认配置JSON',
  `is_active` tinyint(1) DEFAULT 1 COMMENT '是否启用',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_device_type` (`device_type`),
  KEY `idx_is_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='设备模板表';

-- ====================================
-- 初始化数据 (Initial Data)
-- ====================================

-- 插入默认用户
INSERT INTO `users` (`username`, `password_hash`, `role`) VALUES
('admin', 'scrypt:32768:8:1$2b$10$x8jLlWcNtfFIVzwPCGZyZOSGQNwVpFzQzEbQNvqzOGHuNJi3wKl2u', 'admin'),
('user1', 'scrypt:32768:8:1$2b$10$x8jLlWcNtfFIVzwPCGZyZOSGQNwVpFzQzEbQNvqzOGHuNJi3wKl2u', 'user');

-- 插入示例设备
INSERT INTO `devices` (`name`, `location`, `type`, `status`) VALUES
('温室大棚A', '北京农场', 'greenhouse', 'active'),
('温室大棚B', '上海农场', 'greenhouse', 'active'),
('露天菜园', '广州农场', 'open_field', 'active');

-- 插入示例传感器
INSERT INTO `sensors` (`device_id`, `type`, `name`, `unit`, `status`) VALUES
(1, 'temperature', '温度传感器A1', '°C', 'active'),
(1, 'humidity', '湿度传感器A1', '%', 'active'),
(1, 'light', '光照传感器A1', 'lux', 'active'),
(2, 'temperature', '温度传感器B1', '°C', 'active'),
(2, 'humidity', '湿度传感器B1', '%', 'active'),
(2, 'light', '光照传感器B1', 'lux', 'active');

-- 插入默认告警规则
INSERT INTO `alarm_rules` (`name`, `description`, `sensor_id`, `rule_type`, `condition`, `threshold_value`, `consecutive_count`, `severity`, `created_by`) VALUES
('温度过高告警', '温度超过35°C时触发告警', 1, 'threshold', '>', 35.0, 3, 'high', 'system'),
('温度过低告警', '温度低于5°C时触发告警', 1, 'threshold', '<', 5.0, 3, 'medium', 'system'),
('湿度过低告警', '湿度低于20%时触发告警', 2, 'threshold', '<', 20.0, 2, 'medium', 'system'),
('湿度过高告警', '湿度超过90%时触发告警', 2, 'threshold', '>', 90.0, 2, 'low', 'system'),
('光照不足告警', '光照强度低于500lux时触发告警', 3, 'threshold', '<', 500.0, 5, 'low', 'system'),
('温室B温度过高', '温室B温度超过30°C时触发告警', 4, 'threshold', '>', 30.0, 2, 'medium', 'system'),
('温室B湿度异常', '温室B湿度低于30%时触发告警', 5, 'threshold', '<', 30.0, 2, 'medium', 'system');

-- 为每个告警规则创建状态跟踪
INSERT INTO `alarm_states` (`alarm_rule_id`, `consecutive_count`) VALUES
(1, 0), (2, 0), (3, 0), (4, 0), (5, 0), (6, 0), (7, 0);

-- 插入预定义设备模板
INSERT INTO `device_templates` (`device_type`, `name`, `description`, `manufacturer`, `model`, `sensor_configs`, `default_config`) VALUES
('smart_farm', '智慧农场设备', '综合性农业监测设备，包含土壤、环境等多种传感器', 'AgriNex', 'SF-2024',
'[
  {"type": "temperature", "name": "环境温度传感器", "unit": "°C", "description": "监测环境温度", "is_required": true, "validation_rules": {"min": -40, "max": 80}},
  {"type": "humidity", "name": "环境湿度传感器", "unit": "%", "description": "监测空气湿度", "is_required": true, "validation_rules": {"min": 0, "max": 100}},
  {"type": "light", "name": "光照强度传感器", "unit": "lux", "description": "监测光照强度", "is_required": true, "validation_rules": {"min": 0, "max": 10000}},
  {"type": "soil_moisture", "name": "土壤湿度传感器", "unit": "%", "description": "监测土壤含水量", "is_required": true, "validation_rules": {"min": 0, "max": 100}},
  {"type": "soil_ph", "name": "土壤pH传感器", "unit": "pH", "description": "监测土壤酸碱度", "is_required": false, "validation_rules": {"min": 0, "max": 14}},
  {"type": "soil_ec", "name": "土壤EC传感器", "unit": "mS/cm", "description": "监测土壤电导率", "is_required": false, "validation_rules": {"min": 0, "max": 10}}
]',
'{"collection_interval": 30, "data_retention_days": 365, "alert_enabled": true}'),

('weather_station', '气象站设备', '专业气象监测设备，提供全面的天气数据', 'AgriNex', 'WS-2024',
'[
  {"type": "temperature", "name": "气温传感器", "unit": "°C", "description": "监测大气温度", "is_required": true, "validation_rules": {"min": -50, "max": 60}},
  {"type": "humidity", "name": "湿度传感器", "unit": "%", "description": "监测空气湿度", "is_required": true, "validation_rules": {"min": 0, "max": 100}},
  {"type": "pressure", "name": "气压传感器", "unit": "hPa", "description": "监测大气压强", "is_required": true, "validation_rules": {"min": 800, "max": 1200}},
  {"type": "wind_speed", "name": "风速传感器", "unit": "m/s", "description": "监测风速", "is_required": true, "validation_rules": {"min": 0, "max": 50}},
  {"type": "wind_direction", "name": "风向传感器", "unit": "°", "description": "监测风向", "is_required": false, "validation_rules": {"min": 0, "max": 360}},
  {"type": "rain_level", "name": "雨量传感器", "unit": "mm", "description": "监测降雨量", "is_required": false, "validation_rules": {"min": 0, "max": 200}},
  {"type": "uv_index", "name": "UV指数传感器", "unit": "UV", "description": "监测紫外线指数", "is_required": false, "validation_rules": {"min": 0, "max": 15}}
]',
'{"collection_interval": 60, "data_retention_days": 1095, "alert_enabled": true}'),

('environmental_monitor', '环境监测设备', '室内外环境质量监测设备', 'AgriNex', 'EM-2024',
'[
  {"type": "temperature", "name": "温度传感器", "unit": "°C", "description": "监测环境温度", "is_required": true, "validation_rules": {"min": -30, "max": 70}},
  {"type": "humidity", "name": "湿度传感器", "unit": "%", "description": "监测空气湿度", "is_required": true, "validation_rules": {"min": 0, "max": 100}},
  {"type": "co2", "name": "CO2传感器", "unit": "ppm", "description": "监测二氧化碳浓度", "is_required": true, "validation_rules": {"min": 0, "max": 5000}},
  {"type": "noise", "name": "噪音传感器", "unit": "dB", "description": "监测环境噪音", "is_required": false, "validation_rules": {"min": 0, "max": 120}},
  {"type": "light", "name": "光照传感器", "unit": "lux", "description": "监测光照强度", "is_required": false, "validation_rules": {"min": 0, "max": 2000}}
]',
'{"collection_interval": 15, "data_retention_days": 180, "alert_enabled": true}'),

('water_management', '水管理设备', '水质监测和灌溉控制设备', 'AgriNex', 'WM-2024',
'[
  {"type": "water_level", "name": "水位传感器", "unit": "%", "description": "监测水位高度", "is_required": true, "validation_rules": {"min": 0, "max": 100}},
  {"type": "flow_rate", "name": "流量传感器", "unit": "L/min", "description": "监测水流速度", "is_required": true, "validation_rules": {"min": 0, "max": 100}},
  {"type": "pressure", "name": "水压传感器", "unit": "bar", "description": "监测水压", "is_required": true, "validation_rules": {"min": 0, "max": 20}},
  {"type": "temperature", "name": "水温传感器", "unit": "°C", "description": "监测水温", "is_required": false, "validation_rules": {"min": 0, "max": 50}}
]',
'{"collection_interval": 20, "data_retention_days": 365, "alert_enabled": true}'),

-- 新增设备类型预设

('greenhouse_control', '温室控制系统', '智能温室环境控制与监测设备', 'AgriNex', 'GH-2024',
'[
  {"type": "temperature", "name": "温室温度传感器", "unit": "°C", "description": "监测温室内部温度", "is_required": true, "validation_rules": {"min": 0, "max": 50}},
  {"type": "humidity", "name": "温室湿度传感器", "unit": "%", "description": "监测温室内部湿度", "is_required": true, "validation_rules": {"min": 0, "max": 100}},
  {"type": "co2", "name": "CO2浓度传感器", "unit": "ppm", "description": "监测二氧化碳浓度", "is_required": true, "validation_rules": {"min": 300, "max": 2000}},
  {"type": "light", "name": "光照强度传感器", "unit": "lux", "description": "监测光照强度", "is_required": true, "validation_rules": {"min": 0, "max": 100000}},
  {"type": "soil_moisture", "name": "土壤湿度传感器", "unit": "%", "description": "监测土壤含水量", "is_required": true, "validation_rules": {"min": 0, "max": 100}},
  {"type": "soil_temperature", "name": "土壤温度传感器", "unit": "°C", "description": "监测土壤温度", "is_required": false, "validation_rules": {"min": 5, "max": 40}},
  {"type": "wind_speed", "name": "内部风速传感器", "unit": "m/s", "description": "监测温室内风速", "is_required": false, "validation_rules": {"min": 0, "max": 10}}
]',
'{"collection_interval": 10, "data_retention_days": 730, "alert_enabled": true}'),

('soil_monitoring', '土壤监测站', '专业土壤环境监测设备', 'AgriNex', 'SM-2024',
'[
  {"type": "soil_moisture", "name": "土壤湿度传感器", "unit": "%", "description": "监测土壤含水量", "is_required": true, "validation_rules": {"min": 0, "max": 100}},
  {"type": "soil_temperature", "name": "土壤温度传感器", "unit": "°C", "description": "监测土壤温度", "is_required": true, "validation_rules": {"min": -10, "max": 50}},
  {"type": "soil_ph", "name": "土壤pH传感器", "unit": "pH", "description": "监测土壤酸碱度", "is_required": true, "validation_rules": {"min": 3, "max": 10}},
  {"type": "soil_ec", "name": "土壤电导率传感器", "unit": "mS/cm", "description": "监测土壤电导率", "is_required": true, "validation_rules": {"min": 0, "max": 20}},
  {"type": "soil_npk", "name": "土壤NPK传感器", "unit": "mg/kg", "description": "监测土壤氮磷钾含量", "is_required": false, "validation_rules": {"min": 0, "max": 1000}},
  {"type": "soil_organic", "name": "土壤有机质传感器", "unit": "%", "description": "监测土壤有机质含量", "is_required": false, "validation_rules": {"min": 0, "max": 10}}
]',
'{"collection_interval": 60, "data_retention_days": 1095, "alert_enabled": true}'),

('livestock_monitor', '畜牧监测设备', '畜牧场环境与动物健康监测设备', 'AgriNex', 'LM-2024',
'[
  {"type": "temperature", "name": "环境温度传感器", "unit": "°C", "description": "监测畜舍温度", "is_required": true, "validation_rules": {"min": -20, "max": 45}},
  {"type": "humidity", "name": "环境湿度传感器", "unit": "%", "description": "监测畜舍湿度", "is_required": true, "validation_rules": {"min": 0, "max": 100}},
  {"type": "ammonia", "name": "氨气浓度传感器", "unit": "ppm", "description": "监测氨气浓度", "is_required": true, "validation_rules": {"min": 0, "max": 200}},
  {"type": "air_quality", "name": "空气质量传感器", "unit": "AQI", "description": "监测空气质量指数", "is_required": true, "validation_rules": {"min": 0, "max": 500}},
  {"type": "noise", "name": "噪音传感器", "unit": "dB", "description": "监测环境噪音", "is_required": false, "validation_rules": {"min": 30, "max": 120}},
  {"type": "motion", "name": "运动检测传感器", "unit": "count", "description": "检测动物活动", "is_required": false, "validation_rules": {"min": 0, "max": 10000}}
]',
'{"collection_interval": 30, "data_retention_days": 365, "alert_enabled": true}'),

('aquaculture', '水产养殖监测', '水产养殖环境监测设备', 'AgriNex', 'AQ-2024',
'[
  {"type": "water_temperature", "name": "水温传感器", "unit": "°C", "description": "监测水体温度", "is_required": true, "validation_rules": {"min": 0, "max": 40}},
  {"type": "dissolved_oxygen", "name": "溶解氧传感器", "unit": "mg/L", "description": "监测水中溶解氧含量", "is_required": true, "validation_rules": {"min": 0, "max": 20}},
  {"type": "water_ph", "name": "水体pH传感器", "unit": "pH", "description": "监测水体酸碱度", "is_required": true, "validation_rules": {"min": 5, "max": 10}},
  {"type": "turbidity", "name": "浊度传感器", "unit": "NTU", "description": "监测水体浊度", "is_required": true, "validation_rules": {"min": 0, "max": 1000}},
  {"type": "salinity", "name": "盐度传感器", "unit": "ppt", "description": "监测水体盐度", "is_required": false, "validation_rules": {"min": 0, "max": 50}},
  {"type": "water_level", "name": "水位传感器", "unit": "m", "description": "监测水位高度", "is_required": false, "validation_rules": {"min": 0, "max": 10}}
]',
'{"collection_interval": 15, "data_retention_days": 730, "alert_enabled": true}'),

('storage_facility', '仓储监测设备', '农产品仓储环境监测设备', 'AgriNex', 'SF-2024',
'[
  {"type": "temperature", "name": "仓储温度传感器", "unit": "°C", "description": "监测仓库温度", "is_required": true, "validation_rules": {"min": -30, "max": 50}},
  {"type": "humidity", "name": "仓储湿度传感器", "unit": "%", "description": "监测仓库湿度", "is_required": true, "validation_rules": {"min": 0, "max": 100}},
  {"type": "co2", "name": "CO2浓度传感器", "unit": "ppm", "description": "监测二氧化碳浓度", "is_required": true, "validation_rules": {"min": 0, "max": 5000}},
  {"type": "pressure", "name": "气压传感器", "unit": "hPa", "description": "监测气压变化", "is_required": false, "validation_rules": {"min": 900, "max": 1100}},
  {"type": "pest_detection", "name": "害虫检测传感器", "unit": "count", "description": "检测害虫活动", "is_required": false, "validation_rules": {"min": 0, "max": 1000}},
  {"type": "door_sensor", "name": "门禁传感器", "unit": "status", "description": "监测门禁状态", "is_required": false, "validation_rules": {"min": 0, "max": 1}}
]',
'{"collection_interval": 30, "data_retention_days": 365, "alert_enabled": true}'),

('drone_sensor', '无人机传感器', '农业无人机搭载的多功能传感器', 'AgriNex', 'DS-2024',
'[
  {"type": "multispectral", "name": "多光谱传感器", "unit": "index", "description": "监测植被健康指数", "is_required": true, "validation_rules": {"min": 0, "max": 1}},
  {"type": "thermal", "name": "热红外传感器", "unit": "°C", "description": "监测地表温度", "is_required": true, "validation_rules": {"min": -40, "max": 80}},
  {"type": "altitude", "name": "高度传感器", "unit": "m", "description": "监测飞行高度", "is_required": true, "validation_rules": {"min": 0, "max": 500}},
  {"type": "gps_accuracy", "name": "GPS精度传感器", "unit": "m", "description": "监测定位精度", "is_required": true, "validation_rules": {"min": 0, "max": 10}},
  {"type": "battery_level", "name": "电池电量传感器", "unit": "%", "description": "监测电池电量", "is_required": false, "validation_rules": {"min": 0, "max": 100}},
  {"type": "wind_resistance", "name": "抗风能力传感器", "unit": "m/s", "description": "监测当前风阻", "is_required": false, "validation_rules": {"min": 0, "max": 20}}
]',
'{"collection_interval": 5, "data_retention_days": 180, "alert_enabled": true}'),

('irrigation_control', '智能灌溉控制器', '精准灌溉控制与监测设备', 'AgriNex', 'IC-2024',
'[
  {"type": "soil_moisture", "name": "土壤湿度传感器", "unit": "%", "description": "监测土壤含水量", "is_required": true, "validation_rules": {"min": 0, "max": 100}},
  {"type": "flow_rate", "name": "灌溉流量传感器", "unit": "L/min", "description": "监测灌溉流量", "is_required": true, "validation_rules": {"min": 0, "max": 200}},
  {"type": "pressure", "name": "管道压力传感器", "unit": "bar", "description": "监测管道压力", "is_required": true, "validation_rules": {"min": 0, "max": 10}},
  {"type": "valve_status", "name": "阀门状态传感器", "unit": "status", "description": "监测阀门开关状态", "is_required": true, "validation_rules": {"min": 0, "max": 1}},
  {"type": "water_quality", "name": "水质传感器", "unit": "TDS", "description": "监测灌溉水质", "is_required": false, "validation_rules": {"min": 0, "max": 2000}},
  {"type": "pump_status", "name": "水泵状态传感器", "unit": "rpm", "description": "监测水泵转速", "is_required": false, "validation_rules": {"min": 0, "max": 3600}}
]',
'{"collection_interval": 20, "data_retention_days": 365, "alert_enabled": true}');

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
    DECLARE sensor_device_id INT;
    
    -- 获取传感器对应的设备ID
    SELECT device_id INTO sensor_device_id FROM sensors WHERE id = NEW.sensor_id;
    
    -- 温度异常检测 (超出正常范围 0-50度)
    IF NEW.data_type = 'numeric' AND NEW.numeric_value IS NOT NULL THEN
        -- 检查温度传感器
        IF EXISTS (SELECT 1 FROM sensors WHERE id = NEW.sensor_id AND type = 'temperature') THEN
            IF NEW.numeric_value < 0 OR NEW.numeric_value > 50 THEN
                SET anomaly_detected = TRUE;
                INSERT INTO alarms (sensor_id, alarm_type, threshold_value, actual_value, message, severity, created_at)
                VALUES (NEW.sensor_id, 'temperature_anomaly', 25.0, NEW.numeric_value,
                        CONCAT('Temperature out of range: ', NEW.numeric_value, '°C'), 
                        'medium', NOW());
            END IF;
        END IF;
        
        -- 检查湿度传感器 (超出0-100%)
        IF EXISTS (SELECT 1 FROM sensors WHERE id = NEW.sensor_id AND type = 'humidity') THEN
            IF NEW.numeric_value < 0 OR NEW.numeric_value > 100 THEN
                SET anomaly_detected = TRUE;
                INSERT INTO alarms (sensor_id, alarm_type, threshold_value, actual_value, message, severity, created_at)
                VALUES (NEW.sensor_id, 'humidity_anomaly', 50.0, NEW.numeric_value,
                        CONCAT('Humidity out of range: ', NEW.numeric_value, '%'), 
                        'medium', NOW());
            END IF;
        END IF;
        
        -- 检查光照传感器 (负值)
        IF EXISTS (SELECT 1 FROM sensors WHERE id = NEW.sensor_id AND type = 'light') THEN
            IF NEW.numeric_value < 0 THEN
                SET anomaly_detected = TRUE;
                INSERT INTO alarms (sensor_id, alarm_type, threshold_value, actual_value, message, severity, created_at)
                VALUES (NEW.sensor_id, 'light_anomaly', 0.0, NEW.numeric_value,
                        CONCAT('Invalid light reading: ', NEW.numeric_value, ' lux'), 
                        'low', NOW());
            END IF;
        END IF;
    END IF;
END$$
DELIMITER ;

-- ====================================
-- 视图 (Views)
-- ====================================

-- 1. 设备最新状态视图
CREATE VIEW v_device_latest_status AS
SELECT 
    d.id AS device_id,
    d.name AS device_name,
    d.location,
    d.type,
    d.status,
    r.numeric_value,
    r.unit,
    r.timestamp AS last_reading_time,
    CASE 
        WHEN r.timestamp < DATE_SUB(NOW(), INTERVAL 1 HOUR) THEN 'stale'
        WHEN r.timestamp IS NULL THEN 'no_data'
        ELSE 'fresh'
    END AS data_freshness
FROM devices d
LEFT JOIN (
    SELECT sensor_id, numeric_value, unit, timestamp,
           ROW_NUMBER() OVER (PARTITION BY sensor_id ORDER BY timestamp DESC) as rn
    FROM readings
    WHERE data_type = 'numeric'
) r ON d.id IN (SELECT device_id FROM sensors WHERE id = r.sensor_id) AND r.rn = 1;

-- 2. 设备每日统计视图
CREATE VIEW v_device_daily_stats AS
SELECT 
    s.device_id,
    DATE(r.timestamp) AS date,
    COUNT(*) AS reading_count,
    AVG(CASE WHEN s.type = 'temperature' THEN r.numeric_value END) AS avg_temp,
    MIN(CASE WHEN s.type = 'temperature' THEN r.numeric_value END) AS min_temp,
    MAX(CASE WHEN s.type = 'temperature' THEN r.numeric_value END) AS max_temp,
    AVG(CASE WHEN s.type = 'humidity' THEN r.numeric_value END) AS avg_humidity,
    MIN(CASE WHEN s.type = 'humidity' THEN r.numeric_value END) AS min_humidity,
    MAX(CASE WHEN s.type = 'humidity' THEN r.numeric_value END) AS max_humidity,
    AVG(CASE WHEN s.type = 'light' THEN r.numeric_value END) AS avg_light,
    MIN(CASE WHEN s.type = 'light' THEN r.numeric_value END) AS min_light,
    MAX(CASE WHEN s.type = 'light' THEN r.numeric_value END) AS max_light
FROM readings r
JOIN sensors s ON r.sensor_id = s.id
WHERE r.timestamp >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
  AND r.data_type = 'numeric'
GROUP BY s.device_id, DATE(r.timestamp);

-- 3. 活跃告警视图
CREATE VIEW v_active_alarms AS
SELECT 
    a.id,
    a.sensor_id,
    s.name AS sensor_name,
    d.name AS device_name,
    d.location,
    a.alarm_type,
    a.message,
    a.severity,
    a.status,
    a.created_at,
    TIMESTAMPDIFF(MINUTE, a.created_at, NOW()) AS minutes_since_created
FROM alarms a
JOIN sensors s ON a.sensor_id = s.id
JOIN devices d ON s.device_id = d.id
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
        d.id AS device_id,
        d.name,
        d.location,
        d.status,
        MAX(r.timestamp) AS last_reading,
        TIMESTAMPDIFF(HOUR, MAX(r.timestamp), NOW()) AS hours_since_last_reading
    FROM devices d
    LEFT JOIN sensors s ON d.id = s.device_id
    LEFT JOIN readings r ON s.id = r.sensor_id
    WHERE d.status = 'active'
    GROUP BY d.id, d.name, d.location, d.status
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
    SELECT * FROM devices WHERE id = device_id_param;
    
    -- 时间段内的统计
    SELECT 
        COUNT(*) AS total_readings,
        AVG(CASE WHEN s.type = 'temperature' THEN r.numeric_value END) AS avg_temp,
        MIN(CASE WHEN s.type = 'temperature' THEN r.numeric_value END) AS min_temp,
        MAX(CASE WHEN s.type = 'temperature' THEN r.numeric_value END) AS max_temp,
        AVG(CASE WHEN s.type = 'humidity' THEN r.numeric_value END) AS avg_humidity,
        MIN(CASE WHEN s.type = 'humidity' THEN r.numeric_value END) AS min_humidity,
        MAX(CASE WHEN s.type = 'humidity' THEN r.numeric_value END) AS max_humidity,
        AVG(CASE WHEN s.type = 'light' THEN r.numeric_value END) AS avg_light,
        MIN(CASE WHEN s.type = 'light' THEN r.numeric_value END) AS min_light,
        MAX(CASE WHEN s.type = 'light' THEN r.numeric_value END) AS max_light
    FROM readings r
    JOIN sensors s ON r.sensor_id = s.id
    WHERE s.device_id = device_id_param 
      AND r.timestamp >= start_date
      AND r.data_type = 'numeric';
    
    -- 告警统计
    SELECT 
        a.alarm_type,
        COUNT(*) AS alarm_count,
        MAX(a.created_at) AS latest_alarm
    FROM alarms a
    JOIN sensors s ON a.sensor_id = s.id
    WHERE s.device_id = device_id_param AND a.created_at >= start_date
    GROUP BY a.alarm_type;
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
