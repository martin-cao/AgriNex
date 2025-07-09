# backend/services/alarm_service.py
from models.alarm import Alarm
from models.alarm_rule import AlarmRule
from models.alarm_state import AlarmState
from models.reading import Reading
from extensions import db
from datetime import datetime, timedelta
import asyncio
import logging
import json
import requests
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class AlarmService:
    @staticmethod
    def create_alarm(sensor_id, alarm_type, message, actual_value=None, threshold_value=None, severity='medium'):
        """创建告警记录"""
        alarm = Alarm(
            sensor_id=sensor_id,
            alarm_type=alarm_type,
            message=message,
            actual_value=actual_value,
            threshold_value=threshold_value,
            severity=severity
        )
        db.session.add(alarm)
        db.session.commit()
        return alarm

    @staticmethod
    def get_alarms(sensor_id=None, status=None, limit=100):
        """获取告警列表"""
        query = Alarm.query
        if sensor_id:
            query = query.filter_by(sensor_id=sensor_id)
        if status:
            query = query.filter_by(status=status)
        return query.order_by(Alarm.created_at.desc()).limit(limit).all()

    @staticmethod
    def resolve_alarm(alarm_id, resolved_by):
        """解决告警"""
        alarm = Alarm.query.get(alarm_id)
        if alarm:
            alarm.status = 'resolved'
            alarm.resolved_at = datetime.utcnow()
            alarm.resolved_by = resolved_by
            db.session.commit()
            return alarm
        return None

    @staticmethod
    def create_alarm_rule(name, description, sensor_id, rule_type, condition, threshold_value, 
                         consecutive_count=1, severity='medium', created_by='system',
                         email_enabled=False, webhook_enabled=False, webhook_url=None):
        """创建告警规则"""
        rule = AlarmRule(
            name=name,
            description=description,
            sensor_id=sensor_id,
            rule_type=rule_type,
            condition=condition,
            threshold_value=threshold_value,
            consecutive_count=consecutive_count,
            severity=severity,
            created_by=created_by,
            email_enabled=email_enabled,
            webhook_enabled=webhook_enabled,
            webhook_url=webhook_url
        )
        db.session.add(rule)
        db.session.commit()
        
        # 创建对应的状态跟踪
        state = AlarmState(alarm_rule_id=rule.id)
        db.session.add(state)
        db.session.commit()
        
        return rule

    @staticmethod
    def get_alarm_rules(sensor_id=None, is_active=True):
        """获取告警规则列表"""
        query = AlarmRule.query
        if sensor_id:
            query = query.filter_by(sensor_id=sensor_id)
        if is_active is not None:
            query = query.filter_by(is_active=is_active)
        return query.order_by(AlarmRule.created_at.desc()).all()

    @staticmethod
    def update_alarm_rule(rule_id, **kwargs):
        """更新告警规则"""
        rule = AlarmRule.query.get(rule_id)
        if rule:
            for key, value in kwargs.items():
                if hasattr(rule, key):
                    setattr(rule, key, value)
            rule.updated_at = datetime.utcnow()
            db.session.commit()
            return rule
        return None

    @staticmethod
    def delete_alarm_rule(rule_id):
        """删除告警规则"""
        rule = AlarmRule.query.get(rule_id)
        if rule:
            # 删除状态跟踪
            AlarmState.query.filter_by(alarm_rule_id=rule_id).delete()
            db.session.delete(rule)
            db.session.commit()
            return True
        return False

    @staticmethod
    def check_and_trigger_alarms(sensor_id, value, reading_timestamp=None):
        """检查并触发告警"""
        if reading_timestamp is None:
            reading_timestamp = datetime.utcnow()
        
        # 获取该传感器的所有活跃规则
        rules = AlarmRule.query.filter_by(sensor_id=sensor_id, is_active=True).all()
        
        triggered_alarms = []
        
        for rule in rules:
            # 检查条件是否满足
            if rule.evaluate_condition(value):
                # 获取或创建状态跟踪
                state = AlarmState.query.filter_by(alarm_rule_id=rule.id).first()
                if not state:
                    state = AlarmState(alarm_rule_id=rule.id)
                    db.session.add(state)
                
                # 更新连续触发计数
                state.consecutive_count += 1
                state.last_triggered_at = reading_timestamp
                state.last_value = value
                
                # 检查是否达到连续触发次数
                if state.consecutive_count >= rule.consecutive_count:
                    # 创建告警
                    message = f"{rule.name}: {rule.description} (当前值: {value}, 阈值: {rule.threshold_value})"
                    alarm = AlarmService.create_alarm(
                        sensor_id=sensor_id,
                        alarm_type=rule.rule_type,
                        message=message,
                        actual_value=value,
                        threshold_value=rule.threshold_value,
                        severity=rule.severity
                    )
                    triggered_alarms.append(alarm)
                    
                    # 发送通知
                    AlarmService._send_notifications(rule, alarm, value)
                    
                    # 重置计数器（避免重复触发）
                    state.consecutive_count = 0
                
                db.session.commit()
            else:
                # 条件不满足，重置计数器
                state = AlarmState.query.filter_by(alarm_rule_id=rule.id).first()
                if state and state.consecutive_count > 0:
                    state.consecutive_count = 0
                    db.session.commit()
        
        return triggered_alarms

    @staticmethod
    def _send_notifications(rule: AlarmRule, alarm: Alarm, value: float):
        """发送通知"""
        # 邮件通知
        if rule.email_enabled:
            try:
                AlarmService._send_email_notification(rule, alarm, value)
            except Exception as e:
                logger.error(f"Failed to send email notification: {e}")
        
        # Webhook通知
        if rule.webhook_enabled and rule.webhook_url:
            try:
                AlarmService._send_webhook_notification(rule, alarm, value)
            except Exception as e:
                logger.error(f"Failed to send webhook notification: {e}")

    @staticmethod
    def _send_email_notification(rule: AlarmRule, alarm: Alarm, value: float):
        """发送邮件通知（占位实现）"""
        # TODO: 实现邮件发送逻辑
        logger.info(f"Email notification sent for alarm: {alarm.id}")

    @staticmethod
    def _send_webhook_notification(rule: AlarmRule, alarm: Alarm, value: float):
        """发送Webhook通知"""
        payload = {
            "alarm_id": alarm.id,
            "rule_name": rule.name,
            "sensor_id": alarm.sensor_id,
            "alarm_type": alarm.alarm_type,
            "severity": alarm.severity,
            "message": alarm.message,
            "actual_value": value,
            "threshold_value": rule.threshold_value,
            "timestamp": alarm.created_at.isoformat()
        }
        
        try:
            response = requests.post(
                rule.webhook_url,
                json=payload,
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
            logger.info(f"Webhook notification sent successfully for alarm: {alarm.id}")
        except requests.RequestException as e:
            logger.error(f"Failed to send webhook notification: {e}")

    @staticmethod
    def get_alarm_statistics(sensor_id=None, days=7):
        """获取告警统计"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = Alarm.query.filter(Alarm.created_at >= start_date)
        if sensor_id:
            query = query.filter_by(sensor_id=sensor_id)
        
        alarms = query.all()
        
        # 按严重程度统计
        severity_stats = {'low': 0, 'medium': 0, 'high': 0}
        for alarm in alarms:
            severity_stats[alarm.severity] += 1
        
        # 按状态统计
        status_stats = {'active': 0, 'resolved': 0}
        for alarm in alarms:
            status_stats[alarm.status] += 1
        
        return {
            'total_alarms': len(alarms),
            'severity_stats': severity_stats,
            'status_stats': status_stats,
            'period_days': days
        }