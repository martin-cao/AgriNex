# AgriNex 告警系统示例配置

# 默认告警规则模板
DEFAULT_ALARM_RULES = [
    {
        "name": "温度过高告警",
        "description": "温度超过35°C时触发告警",
        "rule_type": "threshold",
        "condition": ">",
        "threshold_value": 35.0,
        "consecutive_count": 3,
        "severity": "high"
    },
    {
        "name": "温度过低告警", 
        "description": "温度低于5°C时触发告警",
        "rule_type": "threshold",
        "condition": "<",
        "threshold_value": 5.0,
        "consecutive_count": 3,
        "severity": "medium"
    },
    {
        "name": "湿度过低告警",
        "description": "湿度低于20%时触发告警",
        "rule_type": "threshold",
        "condition": "<",
        "threshold_value": 20.0,
        "consecutive_count": 2,
        "severity": "medium"
    },
    {
        "name": "湿度过高告警",
        "description": "湿度超过90%时触发告警",
        "rule_type": "threshold",
        "condition": ">",
        "threshold_value": 90.0,
        "consecutive_count": 2,
        "severity": "low"
    },
    {
        "name": "光照不足告警",
        "description": "光照强度低于500lux时触发告警",
        "rule_type": "threshold",
        "condition": "<",
        "threshold_value": 500.0,
        "consecutive_count": 5,
        "severity": "low"
    }
]

# 邮件配置模板
EMAIL_CONFIG = {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_user": "your-email@gmail.com",
    "smtp_password": "your-app-password",
    "from_email": "noreply@agrinex.com",
    "alert_emails": [
        "admin@agrinex.com",
        "alerts@agrinex.com"
    ]
}

# Webhook 配置示例
WEBHOOK_EXAMPLES = {
    "slack": {
        "url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
        "name": "Slack 通知"
    },
    "discord": {
        "url": "https://discord.com/api/webhooks/YOUR/WEBHOOK/URL",
        "name": "Discord 通知"
    },
    "teams": {
        "url": "https://your-tenant.webhook.office.com/webhookb2/YOUR/WEBHOOK/URL",
        "name": "Microsoft Teams 通知"
    }
}

# 告警监控配置
ALARM_MONITOR_CONFIG = {
    "check_interval": 30,  # 检查间隔（秒）
    "batch_size": 100,     # 批处理大小
    "max_retry_attempts": 3,
    "retry_delay": 5
}

# 通知限制配置
NOTIFICATION_LIMITS = {
    "email_rate_limit": 10,      # 每分钟最多10封邮件
    "webhook_rate_limit": 30,    # 每分钟最多30个webhook
    "same_alarm_interval": 300   # 同一告警5分钟内不重复通知
}
