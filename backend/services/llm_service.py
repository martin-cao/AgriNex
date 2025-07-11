# backend/services/llm_service.py
"""
LLM服务 - 提供智能农业建议和对话服务
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import statistics
import openai
import os

logger = logging.getLogger(__name__)

class LLMService:
    """LLM服务类"""
    
    def __init__(self):
        # 配置OpenAI API (可选)
        openai.api_key = os.getenv('OPENAI_API_KEY', '')
        self.use_openai = bool(openai.api_key)
        
        # 农业知识库
        self.agricultural_knowledge = {
            'crops': {
                '番茄': {
                    'optimal_temp': (18, 25),
                    'optimal_humidity': (60, 70),
                    'optimal_soil_moisture': (60, 80),
                    'growth_stages': ['播种', '幼苗', '开花', '结果', '成熟']
                },
                '黄瓜': {
                    'optimal_temp': (20, 30),
                    'optimal_humidity': (70, 80),
                    'optimal_soil_moisture': (70, 85),
                    'growth_stages': ['播种', '幼苗', '开花', '结果', '成熟']
                },
                '生菜': {
                    'optimal_temp': (15, 20),
                    'optimal_humidity': (50, 60),
                    'optimal_soil_moisture': (50, 70),
                    'growth_stages': ['播种', '幼苗', '生长', '成熟']
                }
            },
            'sensors': {
                'temperature': {
                    'name': '温度传感器',
                    'normal_range': (10, 40),
                    'critical_low': 5,
                    'critical_high': 45
                },
                'humidity': {
                    'name': '湿度传感器',
                    'normal_range': (30, 90),
                    'critical_low': 20,
                    'critical_high': 95
                },
                'soil_moisture': {
                    'name': '土壤湿度传感器',
                    'normal_range': (30, 80),
                    'critical_low': 20,
                    'critical_high': 90
                },
                'light': {
                    'name': '光照传感器',
                    'normal_range': (10000, 50000),
                    'critical_low': 5000,
                    'critical_high': 80000
                }
            }
        }
    
    def generate_chat_response(self, message: str, context: str = "", 
                             sensor_context: str = "") -> Dict[str, Any]:
        """生成聊天回复"""
        try:
            # 如果有OpenAI API，使用GPT
            if self.use_openai:
                return self._generate_openai_response(message, context, sensor_context)
            else:
                # 使用内置规则引擎
                return self._generate_rule_based_response(message, context, sensor_context)
                
        except ValueError as e:
            logger.error("Generate chat response error: %s", str(e))
            return {
                'response': '抱歉，我现在无法回答您的问题。请稍后再试。',
                'confidence': 0.1,
                'context': context
            }
        except Exception as e:
            logger.error("Generate chat response error: %s", str(e))
            return {
                'response': '抱歉，我现在无法回答您的问题。请稍后再试。',
                'confidence': 0.1,
                'context': context
            }
    
    def _generate_openai_response(self, message: str, context: str, sensor_context: str) -> Dict[str, Any]:
        """使用OpenAI GPT生成回复"""
        try:
            system_prompt = self._create_system_prompt()
            user_prompt = f"""
            用户消息: {message}
            对话上下文: {context}
            传感器上下文: {sensor_context}
            
            请作为一个专业的农业物联网助手，提供准确、实用的建议。
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            reply = response.choices[0].message.content
            
            return {
                'response': reply,
                'confidence': 0.9,
                'context': context + f"\n用户: {message}\n助手: {reply}"
            }
            
        except ValueError as e:
            logger.error("OpenAI response error: %s", str(e))
            return {
                'response': '抱歉，我现在无法回答您的问题。请稍后再试。',
                'confidence': 0.1,
                'context': context
            }
        except Exception as e:
            logger.error("OpenAI response error: %s", str(e))
            return self._generate_rule_based_response(message, context, sensor_context)
    
    def _generate_rule_based_response(self, message: str, context: str, _sensor_context: str) -> Dict[str, Any]:
        """基于规则的回复生成"""
        # 移除未使用的参数警告
        _ = _sensor_context
        
        message_lower = message.lower()
        
        # 问候语
        if any(word in message_lower for word in ['你好', 'hello', '嗨', '早上好', '下午好']):
            return {
                'response': '您好！我是您的农业物联网助手。我可以帮您分析传感器数据、提供种植建议、诊断系统问题等。请告诉我您需要什么帮助？',
                'confidence': 0.9,
                'context': context
            }
        
        # 温度相关
        if '温度' in message_lower:
            if '高' in message_lower or '热' in message_lower:
                return {
                    'response': '温度过高可能会影响植物生长。建议：\n1. 增加通风或开启风扇\n2. 适当遮阳\n3. 增加湿度来降低体感温度\n4. 检查是否需要调整温控设备',
                    'confidence': 0.8,
                    'context': context
                }
            elif '低' in message_lower or '冷' in message_lower:
                return {
                    'response': '温度过低可能会影响植物生长。建议：\n1. 开启加热设备\n2. 增加保温措施\n3. 检查温室密封性\n4. 关注夜间温度变化',
                    'confidence': 0.8,
                    'context': context
                }
        
        # 湿度相关
        if '湿度' in message_lower:
            if '高' in message_lower:
                return {
                    'response': '湿度过高可能导致病害。建议：\n1. 增加通风换气\n2. 使用除湿设备\n3. 控制浇水量\n4. 检查排水系统',
                    'confidence': 0.8,
                    'context': context
                }
            elif '低' in message_lower:
                return {
                    'response': '湿度过低可能影响植物水分吸收。建议：\n1. 增加喷雾加湿\n2. 在地面洒水\n3. 使用加湿设备\n4. 减少通风时间',
                    'confidence': 0.8,
                    'context': context
                }
        
        # 浇水相关
        if any(word in message_lower for word in ['浇水', '灌溉', '土壤水分']):
            return {
                'response': '关于浇水管理的建议：\n1. 根据土壤湿度传感器数据决定浇水时机\n2. 一般土壤湿度低于30%时需要浇水\n3. 避免在高温时段浇水\n4. 不同作物需水量不同，需要个性化管理',
                'confidence': 0.7,
                'context': context
            }
        
        # 病虫害相关
        if any(word in message_lower for word in ['病虫害', '病害', '虫害', '防治']):
            return {
                'response': '病虫害防治建议：\n1. 定期检查植物健康状况\n2. 保持适宜的温湿度环境\n3. 及时清理病叶残株\n4. 使用生物防治方法\n5. 必要时使用低毒农药',
                'confidence': 0.7,
                'context': context
            }
        
        # 数据分析相关
        if any(word in message_lower for word in ['数据', '分析', '趋势']):
            return {
                'response': '数据分析功能：\n1. 我可以分析您的传感器数据趋势\n2. 识别异常数据点\n3. 提供数据统计报告\n4. 预测未来趋势\n请提供具体的传感器ID或时间范围。',
                'confidence': 0.8,
                'context': context
            }
        
        # 系统问题相关
        if any(word in message_lower for word in ['故障', '问题', '异常', '报警']):
            return {
                'response': '系统问题诊断：\n1. 检查传感器连接状态\n2. 查看最近的告警记录\n3. 验证数据传输是否正常\n4. 检查设备电源和网络连接\n如需详细诊断，请使用系统诊断功能。',
                'confidence': 0.8,
                'context': context
            }
        
        # 默认回复
        return {
            'response': '我理解您的问题。作为农业物联网助手，我可以帮您：\n\n🌱 分析传感器数据和趋势\n📊 提供种植环境建议\n🚨 诊断系统问题\n📈 生成数据报告\n🤖 回答农业相关问题\n\n请告诉我您需要哪方面的帮助？',
            'confidence': 0.6,
            'context': context
        }
    
    def analyze_sensor_data(self, sensor, readings: List) -> Dict[str, Any]:
        """分析传感器数据"""
        try:
            if not readings:
                return {
                    'advice': '暂无数据可分析',
                    'confidence': 0.0,
                    'recommendations': []
                }
            
            # 提取数值
            values = [r.numeric_value for r in readings if r.numeric_value is not None]
            if not values:
                return {
                    'advice': '暂无有效数值数据',
                    'confidence': 0.0,
                    'recommendations': []
                }
            
            # 计算统计信息
            avg_value = statistics.mean(values)
            min_value = min(values)
            max_value = max(values)
            
            # 获取传感器类型的正常范围
            sensor_type = sensor.sensor_type.lower()
            sensor_info = self.agricultural_knowledge['sensors'].get(sensor_type)
            
            advice = f"传感器 {sensor.name} 数据分析：\n"
            advice += f"平均值: {avg_value:.2f} {sensor.unit}\n"
            advice += f"最小值: {min_value:.2f} {sensor.unit}\n"
            advice += f"最大值: {max_value:.2f} {sensor.unit}\n"
            
            recommendations = []
            
            if sensor_info:
                normal_range = sensor_info['normal_range']
                if avg_value < normal_range[0]:
                    advice += f"⚠️ 平均值低于正常范围 ({normal_range[0]}-{normal_range[1]})"
                    recommendations.append(f"考虑提高{sensor_info['name']}数值")
                elif avg_value > normal_range[1]:
                    advice += f"⚠️ 平均值高于正常范围 ({normal_range[0]}-{normal_range[1]})"
                    recommendations.append(f"考虑降低{sensor_info['name']}数值")
                else:
                    advice += f"✅ 数值在正常范围内"
                    
                # 检查极值
                if min_value < sensor_info['critical_low']:
                    recommendations.append(f"警告：最低值达到临界水平，请立即检查")
                if max_value > sensor_info['critical_high']:
                    recommendations.append(f"警告：最高值达到临界水平，请立即检查")
            
            return {
                'advice': advice,
                'confidence': 0.8,
                'recommendations': recommendations
            }
            
        except Exception as e:
            logger.error(f"Analyze sensor data error: {str(e)}")
            return {
                'advice': '数据分析失败',
                'confidence': 0.0,
                'recommendations': []
            }
    
    def generate_agricultural_advice(self, crop_type: str, weather_condition: str,
                                   soil_moisture: Optional[float] = None,
                                   temperature: Optional[float] = None,
                                   humidity: Optional[float] = None) -> Dict[str, Any]:
        """生成农业建议"""
        try:
            advice = f"基于当前环境条件的{crop_type}种植建议：\n\n"
            actions = []
            urgency = "low"
            
            # 获取作物信息
            crop_info = self.agricultural_knowledge['crops'].get(crop_type)
            
            if crop_info:
                # 温度建议
                if temperature is not None:
                    optimal_temp = crop_info['optimal_temp']
                    if temperature < optimal_temp[0]:
                        advice += f"🌡️ 温度偏低（{temperature}°C），建议提高温度至{optimal_temp[0]}-{optimal_temp[1]}°C\n"
                        actions.append("增加温室加热")
                        urgency = "medium"
                    elif temperature > optimal_temp[1]:
                        advice += f"🌡️ 温度偏高（{temperature}°C），建议降低温度至{optimal_temp[0]}-{optimal_temp[1]}°C\n"
                        actions.append("增加通风或遮阳")
                        urgency = "medium"
                    else:
                        advice += f"🌡️ 温度适宜（{temperature}°C）\n"
                
                # 湿度建议
                if humidity is not None:
                    optimal_humidity = crop_info['optimal_humidity']
                    if humidity < optimal_humidity[0]:
                        advice += f"💧 湿度偏低（{humidity}%），建议提高湿度至{optimal_humidity[0]}-{optimal_humidity[1]}%\n"
                        actions.append("增加喷雾加湿")
                    elif humidity > optimal_humidity[1]:
                        advice += f"💧 湿度偏高（{humidity}%），建议降低湿度至{optimal_humidity[0]}-{optimal_humidity[1]}%\n"
                        actions.append("增加通风除湿")
                    else:
                        advice += f"💧 湿度适宜（{humidity}%）\n"
                
                # 土壤水分建议
                if soil_moisture is not None:
                    optimal_moisture = crop_info['optimal_soil_moisture']
                    if soil_moisture < optimal_moisture[0]:
                        advice += f"🌱 土壤湿度偏低（{soil_moisture}%），建议灌溉\n"
                        actions.append("进行灌溉")
                        urgency = "high"
                    elif soil_moisture > optimal_moisture[1]:
                        advice += f"🌱 土壤湿度偏高（{soil_moisture}%），注意排水\n"
                        actions.append("检查排水系统")
                        urgency = "medium"
                    else:
                        advice += f"🌱 土壤湿度适宜（{soil_moisture}%）\n"
            
            # 天气条件建议
            if weather_condition == "晴天":
                advice += "\n☀️ 晴天建议：\n- 注意遮阳防高温\n- 适量增加浇水\n- 保持良好通风\n"
            elif weather_condition == "雨天":
                advice += "\n🌧️ 雨天建议：\n- 注意排水防涝\n- 减少浇水频率\n- 预防病害发生\n"
            elif weather_condition == "阴天":
                advice += "\n☁️ 阴天建议：\n- 可能需要补充光照\n- 注意保温\n- 控制湿度\n"
            
            # 通用建议
            advice += "\n📋 日常管理建议：\n"
            advice += "- 定期检查植物健康状况\n"
            advice += "- 保持环境清洁\n"
            advice += "- 记录管理日志\n"
            advice += "- 关注天气预报\n"
            
            return {
                'advice': advice,
                'actions': actions,
                'urgency': urgency
            }
            
        except Exception as e:
            logger.error(f"Generate agricultural advice error: {str(e)}")
            return {
                'advice': '暂无法生成建议',
                'actions': [],
                'urgency': 'low'
            }
    
    def generate_report(self, sensors_data: List[Dict], report_type: str,
                       start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """生成智能报告"""
        try:
            report = f"农业物联网系统{report_type}报告\n"
            report += f"时间范围: {start_date.strftime('%Y-%m-%d %H:%M')} - {end_date.strftime('%Y-%m-%d %H:%M')}\n\n"
            
            summary = []
            recommendations = []
            
            for sensor_data in sensors_data:
                sensor = sensor_data['sensor']
                readings = sensor_data['readings']
                
                if not readings:
                    continue
                
                values = [r.numeric_value for r in readings if r.numeric_value is not None]
                if not values:
                    continue
                
                report += f"📊 {sensor.name} ({sensor.sensor_type})\n"
                report += f"   数据点数: {len(values)}\n"
                report += f"   平均值: {statistics.mean(values):.2f} {sensor.unit}\n"
                report += f"   最小值: {min(values):.2f} {sensor.unit}\n"
                report += f"   最大值: {max(values):.2f} {sensor.unit}\n\n"
                
                # 数据质量评估
                if len(values) < 10:
                    summary.append(f"{sensor.name}数据点较少，建议检查传感器连接")
                
                # 异常值检测
                avg_val = statistics.mean(values)
                if len(values) > 1:
                    std_dev = statistics.stdev(values)
                    outliers = [v for v in values if abs(v - avg_val) > 2 * std_dev]
                    if outliers:
                        summary.append(f"{sensor.name}检测到{len(outliers)}个异常值")
                        recommendations.append(f"检查{sensor.name}的异常数据")
            
            # 系统总结
            report += "📈 报告总结:\n"
            for item in summary:
                report += f"- {item}\n"
            
            if not summary:
                report += "- 系统运行正常，数据质量良好\n"
            
            return {
                'report': report,
                'summary': "系统运行正常" if not summary else f"发现{len(summary)}个问题需要关注",
                'recommendations': recommendations
            }
            
        except Exception as e:
            logger.error(f"Generate report error: {str(e)}")
            return {
                'report': '报告生成失败',
                'summary': '无法生成报告',
                'recommendations': []
            }
    
    def generate_system_diagnosis(self, devices_count: int, sensors_count: int,
                                active_alarms: int, recent_readings: int,
                                problem_sensors: List) -> Dict[str, Any]:
        """生成系统诊断"""
        try:
            diagnosis = "🔍 系统诊断报告\n\n"
            
            # 系统概览
            diagnosis += f"📊 系统概览:\n"
            diagnosis += f"- 活跃设备数: {devices_count}\n"
            diagnosis += f"- 活跃传感器数: {sensors_count}\n"
            diagnosis += f"- 活跃告警数: {active_alarms}\n"
            diagnosis += f"- 24小时数据点: {recent_readings}\n\n"
            
            # 健康评分计算
            health_score = 100
            recommendations = []
            priority_actions = []
            
            # 告警影响评分
            if active_alarms > 0:
                health_score -= min(active_alarms * 10, 30)
                recommendations.append(f"处理{active_alarms}个活跃告警")
                if active_alarms > 5:
                    priority_actions.append("立即处理紧急告警")
            
            # 数据质量评分
            expected_readings = sensors_count * 24  # 假设每小时一个数据点
            if expected_readings > 0:
                data_quality = recent_readings / expected_readings
                if data_quality < 0.5:
                    health_score -= 20
                    recommendations.append("检查数据采集频率")
                elif data_quality < 0.8:
                    health_score -= 10
                    recommendations.append("优化数据采集")
            
            # 问题传感器评分
            if problem_sensors:
                health_score -= min(len(problem_sensors) * 5, 25)
                recommendations.append(f"修复{len(problem_sensors)}个问题传感器")
                if len(problem_sensors) > 3:
                    priority_actions.append("检查传感器连接")
            
            # 生成诊断结果
            if health_score >= 90:
                diagnosis += "✅ 系统健康状况: 优秀\n"
                diagnosis += "系统运行正常，所有组件工作良好。\n"
            elif health_score >= 70:
                diagnosis += "⚠️ 系统健康状况: 良好\n"
                diagnosis += "系统基本正常，有少量问题需要关注。\n"
            elif health_score >= 50:
                diagnosis += "⚠️ 系统健康状况: 一般\n"
                diagnosis += "系统存在一些问题，需要及时处理。\n"
            else:
                diagnosis += "❌ 系统健康状况: 差\n"
                diagnosis += "系统存在严重问题，需要立即处理。\n"
            
            diagnosis += f"\n🎯 健康评分: {health_score}/100\n"
            
            if recommendations:
                diagnosis += "\n📋 建议措施:\n"
                for rec in recommendations:
                    diagnosis += f"- {rec}\n"
            
            if priority_actions:
                diagnosis += "\n🚨 优先处理:\n"
                for action in priority_actions:
                    diagnosis += f"- {action}\n"
            
            return {
                'diagnosis': diagnosis,
                'health_score': health_score,
                'recommendations': recommendations,
                'priority_actions': priority_actions
            }
            
        except Exception as e:
            logger.error(f"Generate system diagnosis error: {str(e)}")
            return {
                'diagnosis': '系统诊断失败',
                'health_score': 0,
                'recommendations': [],
                'priority_actions': []
            }
    
    def generate_quick_actions(self, active_alarms: List) -> List[Dict[str, Any]]:
        """生成快捷操作"""
        try:
            actions = []
            
            # 基础快捷操作
            actions.extend([
                {
                    'id': 'system_status',
                    'label': '系统状态检查',
                    'type': 'primary',
                    'description': '检查系统整体运行状态',
                    'action': 'system_diagnosis'
                },
                {
                    'id': 'sensor_summary',
                    'label': '传感器概览',
                    'type': 'info',
                    'description': '查看所有传感器状态',
                    'action': 'sensor_summary'
                },
                {
                    'id': 'today_report',
                    'label': '今日报告',
                    'type': 'success',
                    'description': '生成今日数据报告',
                    'action': 'generate_report'
                }
            ])
            
            # 基于告警的快捷操作
            if active_alarms:
                actions.insert(0, {
                    'id': 'handle_alarms',
                    'label': f'处理告警({len(active_alarms)})',
                    'type': 'danger',
                    'description': f'处理{len(active_alarms)}个活跃告警',
                    'action': 'handle_alarms'
                })
            
            return actions
            
        except Exception as e:
            logger.error(f"Generate quick actions error: {str(e)}")
            return []
    
    def _create_system_prompt(self) -> str:
        """创建系统提示"""
        return """
        你是一个专业的农业物联网助手，具备以下能力：
        
        1. 农业知识：了解各种作物的生长需求、最适环境条件
        2. 传感器数据分析：能够分析温度、湿度、土壤湿度、光照等传感器数据
        3. 系统诊断：能够识别系统问题并提供解决方案
        4. 智能建议：基于环境数据提供种植管理建议
        
        回答时请：
        - 使用简洁明了的语言
        - 提供具体可行的建议
        - 使用适当的表情符号增强可读性
        - 根据数据严重程度给出相应的紧急级别
        - 保持专业和友好的语调
        """
