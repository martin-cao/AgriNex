# backend/services/notification_service.py
import smtplib
import requests
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any
from flask import current_app
from models.alarm import Alarm
from models.alarm_rule import AlarmRule

logger = logging.getLogger(__name__)

class NotificationService:
    """通知服务"""
    
    @staticmethod
    def send_alarm_notification(alarm: Alarm, rule: AlarmRule):
        """发送告警通知"""
        try:
            # 发送邮件通知
            if rule.email_enabled:
                NotificationService._send_email_notification(alarm, rule)
            
            # 发送Webhook通知
            if rule.webhook_enabled and rule.webhook_url:
                NotificationService._send_webhook_notification(alarm, rule)
                
        except Exception as e:
            logger.error(f"Failed to send notification for alarm {alarm.id}: {e}")
    
    @staticmethod
    def _send_email_notification(alarm: Alarm, rule: AlarmRule):
        """发送邮件通知"""
        try:
            # 获取邮件配置
            smtp_server = current_app.config.get('SMTP_SERVER')
            smtp_port = current_app.config.get('SMTP_PORT', 587)
            smtp_user = current_app.config.get('SMTP_USER')
            smtp_password = current_app.config.get('SMTP_PASSWORD')
            from_email = current_app.config.get('FROM_EMAIL', smtp_user)
            to_emails = current_app.config.get('ALERT_EMAILS', [])
            
            if not all([smtp_server, smtp_user, smtp_password, to_emails]):
                logger.warning("Email configuration incomplete, skipping email notification")
                return
            
            # 构建邮件内容
            subject = f"AgriNex 告警: {rule.name}"
            
            html_content = f"""
            <html>
            <body>
                <h2>AgriNex 系统告警</h2>
                <p><strong>告警名称:</strong> {rule.name}</p>
                <p><strong>传感器ID:</strong> {alarm.sensor_id}</p>
                <p><strong>告警类型:</strong> {alarm.alarm_type}</p>
                <p><strong>严重程度:</strong> {alarm.severity}</p>
                <p><strong>当前值:</strong> {alarm.actual_value}</p>
                <p><strong>阈值:</strong> {alarm.threshold_value}</p>
                <p><strong>触发时间:</strong> {alarm.created_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>描述:</strong> {alarm.message}</p>
                <hr>
                <p><small>此邮件由 AgriNex 农业物联网平台自动发送</small></p>
            </body>
            </html>
            """
            
            # 发送邮件
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = from_email
            msg['To'] = ', '.join(to_emails)
            
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email notification sent for alarm {alarm.id}")
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
    
    @staticmethod
    def _send_webhook_notification(alarm: Alarm, rule: AlarmRule):
        """发送Webhook通知"""
        try:
            payload = {
                "event": "alarm_triggered",
                "alarm": {
                    "id": alarm.id,
                    "rule_name": rule.name,
                    "sensor_id": alarm.sensor_id,
                    "alarm_type": alarm.alarm_type,
                    "severity": alarm.severity,
                    "message": alarm.message,
                    "actual_value": alarm.actual_value,
                    "threshold_value": alarm.threshold_value,
                    "created_at": alarm.created_at.isoformat()
                },
                "rule": {
                    "id": rule.id,
                    "name": rule.name,
                    "description": rule.description,
                    "condition": rule.condition,
                    "threshold_value": rule.threshold_value
                }
            }
            
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'AgriNex-Alert-System/1.0'
            }
            
            response = requests.post(
                rule.webhook_url,
                json=payload,
                headers=headers,
                timeout=10
            )
            
            response.raise_for_status()
            logger.info(f"Webhook notification sent for alarm {alarm.id}")
            
        except requests.RequestException as e:
            logger.error(f"Failed to send webhook notification: {e}")
    
    @staticmethod
    def send_test_notification(notification_type: str, config: Dict[str, Any]):
        """发送测试通知"""
        try:
            if notification_type == 'email':
                NotificationService._send_test_email(config)
            elif notification_type == 'webhook':
                NotificationService._send_test_webhook(config)
            else:
                raise ValueError(f"Unsupported notification type: {notification_type}")
                
        except Exception as e:
            logger.error(f"Failed to send test notification: {e}")
            raise
    
    @staticmethod
    def _send_test_email(config: Dict[str, Any]):
        """发送测试邮件"""
        smtp_server = config.get('smtp_server')
        smtp_port = config.get('smtp_port', 587)
        smtp_user = config.get('smtp_user')
        smtp_password = config.get('smtp_password')
        to_email = config.get('to_email')
        
        if not all([smtp_server, smtp_user, smtp_password, to_email]):
            raise ValueError("Email configuration incomplete")
        
        subject = "AgriNex 测试邮件"
        content = "这是一封来自 AgriNex 农业物联网平台的测试邮件。"
        
        msg = MIMEText(content, 'plain', 'utf-8')
        msg['Subject'] = subject
        msg['From'] = smtp_user
        msg['To'] = to_email
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
    
    @staticmethod
    def _send_test_webhook(config: Dict[str, Any]):
        """发送测试Webhook"""
        webhook_url = config.get('webhook_url')
        
        if not webhook_url:
            raise ValueError("Webhook URL is required")
        
        payload = {
            "event": "test_notification",
            "message": "这是来自 AgriNex 农业物联网平台的测试通知",
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'AgriNex-Alert-System/1.0'
        }
        
        response = requests.post(
            webhook_url,
            json=payload,
            headers=headers,
            timeout=10
        )
        
        response.raise_for_status()
