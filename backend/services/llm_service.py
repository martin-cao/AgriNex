# backend/services/llm_service.py
"""
LLM服务 - 提供智能农业建议和对话服务
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Generator
import json
import statistics
import os

logger = logging.getLogger(__name__)

class LLMService:
    """LLM服务类"""
    
    def __init__(self):
        # 配置OpenAI API (支持第三方API)
        self.api_key = os.getenv('OPENAI_API_KEY', '')
        self.base_url = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
        self.model = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
        self.use_openai = bool(self.api_key)
        
        # 初始化OpenAI客户端
        self.client = None
        if self.use_openai:
            try:
                from openai import OpenAI
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url
                )
                logger.info(f"OpenAI客户端初始化成功: {self.base_url}, 模型: {self.model}")
            except Exception as e:
                logger.error(f"OpenAI客户端初始化失败: {str(e)}")
                self.use_openai = False
        
        # 农业知识库 - 增强版
        self.agricultural_knowledge = {
            'crops': {
                '番茄': {
                    'optimal_temp': (18, 25),
                    'optimal_humidity': (60, 70),
                    'optimal_soil_moisture': (60, 80),
                    'optimal_ph': (6.0, 6.8),
                    'optimal_ec': (2.0, 3.5),  # mS/cm
                    'growth_stages': ['播种', '幼苗', '开花', '结果', '成熟'],
                    'irrigation_frequency': '每天1-2次',
                    'light_requirement': '12-16小时/天',
                    'common_diseases': ['晚疫病', '灰霉病', '病毒病'],
                    'harvest_period': '90-120天'
                },
                '黄瓜': {
                    'optimal_temp': (20, 30),
                    'optimal_humidity': (70, 80),
                    'optimal_soil_moisture': (70, 85),
                    'optimal_ph': (5.8, 6.5),
                    'optimal_ec': (1.8, 2.8),
                    'growth_stages': ['播种', '幼苗', '开花', '结果', '成熟'],
                    'irrigation_frequency': '每天2-3次',
                    'light_requirement': '10-12小时/天',
                    'common_diseases': ['霜霉病', '白粉病', '细菌性角斑病'],
                    'harvest_period': '60-80天'
                },
                '生菜': {
                    'optimal_temp': (15, 20),
                    'optimal_humidity': (50, 60),
                    'optimal_soil_moisture': (50, 70),
                    'optimal_ph': (6.0, 7.0),
                    'optimal_ec': (1.2, 2.0),
                    'growth_stages': ['播种', '幼苗', '生长', '成熟'],
                    'irrigation_frequency': '每天1次',
                    'light_requirement': '8-10小时/天',
                    'common_diseases': ['软腐病', '霜霉病', '菌核病'],
                    'harvest_period': '30-50天'
                }
            },
            'sensors': {
                'temperature': {
                    'name': '温度传感器',
                    'normal_range': (10, 40),
                    'critical_low': 5,
                    'critical_high': 45,
                    'unit': '°C',
                    'accuracy': '±0.5°C'
                },
                'humidity': {
                    'name': '湿度传感器',
                    'normal_range': (30, 90),
                    'critical_low': 20,
                    'critical_high': 95,
                    'unit': '%RH',
                    'accuracy': '±3%RH'
                },
                'soil_moisture': {
                    'name': '土壤湿度传感器',
                    'normal_range': (30, 80),
                    'critical_low': 20,
                    'critical_high': 90,
                    'unit': '%',
                    'accuracy': '±2%'
                },
                'light': {
                    'name': '光照传感器',
                    'normal_range': (10000, 50000),
                    'critical_low': 5000,
                    'critical_high': 80000,
                    'unit': 'Lux',
                    'accuracy': '±5%'
                },
                'ph': {
                    'name': 'pH传感器',
                    'normal_range': (5.5, 7.5),
                    'critical_low': 4.5,
                    'critical_high': 8.5,
                    'unit': 'pH',
                    'accuracy': '±0.1pH'
                },
                'ec': {
                    'name': 'EC传感器',
                    'normal_range': (1.0, 4.0),
                    'critical_low': 0.5,
                    'critical_high': 5.0,
                    'unit': 'mS/cm',
                    'accuracy': '±2%'
                }
            },
            'alerts': {
                'temperature': {
                    'too_high': '🔴 温度过高警报：可能导致植物热胁迫、花粉不育、果实品质下降',
                    'too_low': '🔴 温度过低警报：可能导致生长缓慢、根系活力下降、易感病害',
                    'optimal': '🟢 温度适宜：有利于植物正常生长发育'
                },
                'humidity': {
                    'too_high': '🟡 湿度过高警报：可能导致病害滋生、根部缺氧、果实裂果',
                    'too_low': '🟡 湿度过低警报：可能导致蒸腾过度、叶片萎蔫、产量下降',
                    'optimal': '🟢 湿度适宜：有利于植物水分平衡和正常代谢'
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
        except Exception as e:
            logger.error(f"生成回复失败: {str(e)}")
            return {
                'response': '抱歉，我现在无法处理您的问题，请稍后再试。',
                'confidence': 0.1,
                'context': context
            }
    
    def generate_chat_response_stream(self, message: str, context: str = "", 
                                    sensor_context: str = "") -> Generator[str, None, None]:
        """生成流式聊天回复"""
        try:
            # 如果有OpenAI API，使用GPT流式响应
            if self.use_openai:
                yield from self._generate_openai_response_stream(message, context, sensor_context)
            else:
                # 使用内置规则引擎（模拟流式输出）
                response = self._generate_rule_based_response(message, context, sensor_context)
                # 将响应分块输出，模拟流式效果
                response_text = response['response']
                chunk_size = 10  # 每块字符数
                for i in range(0, len(response_text), chunk_size):
                    chunk = response_text[i:i + chunk_size]
                    yield chunk
                    # 模拟网络延迟
                    import time
                    time.sleep(0.05)
        except Exception as e:
            logger.error(f"生成流式回复失败: {str(e)}")
            yield "抱歉，我现在无法处理您的问题，请稍后再试。"
    
    def _generate_openai_response_stream(self, message: str, context: str, sensor_context: str) -> Generator[str, None, None]:
        """使用OpenAI GPT生成流式回复"""
        try:
            if not self.client:
                logger.warning("OpenAI客户端未初始化，使用规则引擎")
                response = self._generate_rule_based_response(message, context, sensor_context)
                # 模拟流式输出
                response_text = response['response']
                chunk_size = 10
                for i in range(0, len(response_text), chunk_size):
                    yield response_text[i:i + chunk_size]
                    import time
                    time.sleep(0.05)
                return
                
            system_prompt = self._create_system_prompt()
            
            # 构建结构化的用户输入
            user_prompt = f"""
            ## 用户咨询
            {message}
            
            ## 历史对话
            {context if context else "这是新的对话"}
            
            ## 当前传感器数据
            {sensor_context if sensor_context else "使用系统预设的示例数据进行分析"}
            
            ## 请求响应
            请作为AgriNex农业专家，基于您的专业知识和可用数据为用户提供实用的指导建议。
            """
            
            # 调用OpenAI流式API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=800,
                stream=True  # 启用流式输出
            )
            
            # 逐个yield响应块
            for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"OpenAI流式响应失败: {str(e)}")
            yield "抱歉，AI服务暂时不可用，请稍后再试。"
    
    def _generate_openai_response(self, message: str, context: str, sensor_context: str) -> Dict[str, Any]:
        """使用OpenAI GPT生成回复"""
        try:
            if not self.client:
                logger.warning("OpenAI客户端未初始化，使用规则引擎")
                return self._generate_rule_based_response(message, context, sensor_context)
                
            system_prompt = self._create_system_prompt()
            
            # 构建结构化的用户输入
            user_prompt = f"""
            ## 用户咨询
            {message}
            
            ## 历史对话
            {context if context else "这是新的对话"}
            
            ## 当前传感器数据
            {sensor_context if sensor_context else "使用系统预设的示例数据进行分析"}
            
            ## 请求响应
            请作为AgriNex农业专家，基于您的专业知识和可用数据为用户提供实用的指导建议。
            如果涉及数据异常，请标注紧急程度并给出具体的解决步骤。
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=800,  # 增加token限制以获得更详细的回答
                temperature=0.3,  # 降低温度以获得更一致和准确的回答
                top_p=0.9,  # 控制回答的多样性
                frequency_penalty=0.1,  # 减少重复内容
                presence_penalty=0.1  # 鼓励多样化的表达
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
                'response': '''🌱 **AgriNex智能农业助手为您服务！**

我可以为您提供以下专业服务：
📊 **传感器数据分析** - 温度、湿度、土壤湿度、光照、pH、EC值
🌿 **作物管理建议** - 番茄、黄瓜、生菜等作物的种植指导
⚠️ **异常预警诊断** - 环境异常、设备故障、病虫害风险
💡 **智能决策支持** - 灌溉、施肥、温控等精准管理

请告诉我您当前遇到的问题，我会为您提供专业的解决方案！''',
                'confidence': 0.9,
                'context': context
            }
        
        # 温度相关
        if '温度' in message_lower:
            if '高' in message_lower or '热' in message_lower:
                return {
                    'response': '''🔴 **温度过高警报**

当前温度可能已超出作物适宜范围，建议立即采取以下措施：

🌬️ **通风降温**
   - 开启排风扇或通风设备
   - 增加空气流通速度

☂️ **遮阳降温**
   - 启用遮阳网（50-70%遮光率）
   - 避免强光直射

💧 **湿度调节**
   - 适当增加湿度降低体感温度
   - 地面喷水降温

⚙️ **设备检查**
   - 检查温控设备是否正常运行
   - 调整自动化控制参数''',
                    'confidence': 0.8,
                    'context': context
                }
            elif '低' in message_lower or '冷' in message_lower:
                return {
                    'response': '''🔴 **温度过低警报**

当前温度可能影响作物正常生长，建议立即采取以下措施：

🔥 **加热保温**
   - 开启加热设备或暖风机
   - 检查加热系统运行状态

🏠 **保温措施**
   - 检查温室密封性
   - 加装保温材料

🌙 **夜间管理**
   - 特别关注夜间温度变化
   - 设置最低温度警报

📊 **监控调整**
   - 密切监控温度趋势
   - 调整自动化控制策略''',
                    'confidence': 0.8,
                    'context': context
                }
        
        # 湿度相关
        if '湿度' in message_lower:
            if '高' in message_lower:
                return {
                    'response': '''🟡 **湿度过高警报**

高湿度环境容易引发病害，建议采取以下措施：

🌬️ **通风除湿**
   - 增加通风换气频率
   - 使用除湿设备

💧 **水分控制**
   - 控制浇水量和频次
   - 检查排水系统是否畅通

🦠 **病害预防**
   - 加强植物健康监测
   - 预防性使用生物菌剂

📈 **数据监控**
   - 设置湿度上限报警
   - 记录湿度变化趋势''',
                    'confidence': 0.8,
                    'context': context
                }
            elif '低' in message_lower:
                return {
                    'response': '''🟡 **湿度过低警报**

低湿度可能影响植物水分吸收，建议：

💨 **增湿措施**
   - 使用喷雾系统增加空气湿度
   - 在地面适量洒水

🌊 **水分管理**
   - 适当增加灌溉频次
   - 保持土壤适宜湿度

🔧 **设备调整**
   - 减少过度通风
   - 使用加湿设备

📊 **环境平衡**
   - 平衡温湿度关系
   - 避免湿度过度波动''',
                    'confidence': 0.8,
                    'context': context
                }
        
        # 浇水相关
        if any(word in message_lower for word in ['浇水', '灌溉', '土壤水分']):
            return {
                'response': '''💧 **智能灌溉管理建议**

**判断浇水时机：**
🔍 土壤湿度 < 30% → 需要立即浇水
🔍 土壤湿度 30-50% → 准备浇水
🔍 土壤湿度 > 70% → 暂缓浇水

**最佳浇水策略：**
⏰ 早晨6-8点或傍晚6-8点浇水
🌡️ 避免高温时段（12-15点）
💧 少量多次，避免积水
🎯 根据作物类型调整水量

**作物需水参考：**
🍅 番茄：土壤湿度保持60-80%
🥒 黄瓜：土壤湿度保持70-85%
🥬 生菜：土壤湿度保持50-70%''',
                'confidence': 0.7,
                'context': context
            }
        
        # 病虫害相关
        if any(word in message_lower for word in ['病虫害', '病害', '虫害', '防治']):
            return {
                'response': '''🦠 **病虫害综合防治策略**

**预防为主：**
🌡️ 保持适宜的温湿度环境
🧹 及时清理病叶残株
🔄 合理轮作，避免连作
💨 保证良好通风

**生物防治：**
🐛 使用生物菌剂和天敌
🌿 种植驱虫植物
🦋 维护生态平衡

**化学防治：**
⚗️ 必要时使用低毒农药
⏰ 严格按照用药间隔期
📏 精确控制用药剂量

**常见病害特征：**
🍅 晚疫病：叶片出现水渍状斑点
🦠 灰霉病：果实出现灰色霉层
🔴 病毒病：叶片黄化扭曲''',
                'confidence': 0.7,
                'context': context
            }
        
        # 数据分析相关
        if any(word in message_lower for word in ['数据', '分析', '趋势']):
            return {
                'response': '''📊 **智能数据分析服务**

**我可以为您分析：**
📈 传感器数据趋势变化
⚠️ 异常数据点识别
📋 环境数据统计报告
🔮 未来趋势预测分析

**分析维度包括：**
🌡️ 温度变化规律
💧 湿度波动分析
🌱 土壤状态评估
☀️ 光照条件分析

**获取分析报告：**
请提供具体的传感器ID或时间范围
例如："分析1号温度传感器最近7天数据"
或者："生成本周环境数据报告"''',
                'confidence': 0.8,
                'context': context
            }
        
        # 系统问题相关
        if any(word in message_lower for word in ['故障', '问题', '异常', '报警']):
            return {
                'response': '''🔧 **系统故障诊断指南**

**网络连接检查：**
🌐 确认设备网络连接状态
📡 检查MQTT服务器连接
🔗 验证API接口响应

**传感器状态检查：**
⏰ 查看数据更新时间戳
🔌 检查传感器电源连线
📏 确认传感器校准状态

**设备重启方案：**
🔄 重启相关IoT设备
📶 重新连接网络
📋 检查系统运行日志

**获取详细诊断：**
请描述具体故障现象
提供错误代码或截图
我会给出针对性解决方案''',
                'confidence': 0.8,
                'context': context
            }
        
        # 默认回复
        return {
            'response': '''� **AgriNex智能助手** 

我可以帮您解决各种农业物联网问题：

🌱 **作物管理** - 环境调控、生长监测
📊 **数据分析** - 趋势分析、异常检测  
🚨 **故障诊断** - 设备检修、系统优化
💡 **智能建议** - 灌溉、施肥、病虫害防治

**使用建议：**
• 描述具体问题："番茄叶片发黄怎么办"
• 提供环境数据："温度28度是否正常"
• 请求数据分析："分析最近的湿度趋势"

期待为您的智慧农业提供专业支持！''',
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
        你是AgriNex智能农业物联网平台的专业AI助手，专精于现代农业技术和数据分析。

        ## 当前农场状态（示例数据，如有实时数据请优先使用）
        🌡️ 环境温度：22.5°C（适宜范围）
        💧 环境湿度：65%（适宜范围）  
        🌱 土壤湿度：58%（轻微偏低）
        ☀️ 光照强度：25,000 Lux（良好）
        🧪 土壤pH：6.2（适宜）
        ⚡ EC值：2.1 mS/cm（正常）

        ## 核心能力
        1. **精准农业分析**: 深度理解作物生理需求，熟悉番茄、黄瓜、生菜等常见作物的最适生长环境参数
        2. **IoT数据解读**: 精通传感器数据分析，包括温度(10-40°C)、湿度(30-90%)、土壤湿度(30-80%)、光照强度等环境指标
        3. **预警诊断**: 能识别环境异常、设备故障、病虫害风险，并提供预防性解决方案
        4. **智能决策**: 基于实时数据和历史趋势，提供灌溉、施肥、温控等精准管理建议
        5. **系统优化**: 协助用户优化农场自动化设备和物联网系统配置

        ## 专业知识库
        - **番茄**: 最适温度18-25°C，湿度60-70%，土壤湿度60-80%，pH 6.0-6.8
        - **黄瓜**: 最适温度20-30°C，湿度70-80%，土壤湿度70-85%，pH 5.8-6.5  
        - **生菜**: 最适温度15-20°C，湿度50-60%，土壤湿度50-70%，pH 6.0-7.0
        - **灌溉管理**: 早晨7-9点和傍晚5-7点为最佳灌溉时间
        - **病虫害防控**: 基于环境数据的早期预警和生物防治方案

        ## 常见问题处理指南
        - **用户询问一般农业问题**: 直接基于农业知识和示例数据回答，无需要求额外数据
        - **用户询问具体诊断**: 如有实时数据则使用，否则基于示例数据和经验给出建议
        - **用户咨询设备操作**: 提供标准操作流程和参数设置建议
        - **用户问候或闲聊**: 友好回应并主动介绍可以提供的农业服务

        ## 回答规范
        - 🎯 **主动服务**: 无需等待完整数据，基于现有信息积极提供建议
        - ⚡ **时效性**: 根据情况标注优先级（🔴紧急/🟡注意/🟢正常）
        - 📊 **数据驱动**: 优先使用实时数据，其次使用示例数据
        - 🛠️ **可执行**: 给出详细的设备操作指导和参数设置建议
        - 🌱 **科学性**: 基于农业科学原理，确保建议的科学性和安全性
        - 💬 **友好专业**: 保持温和耐心的语调，用易懂的语言解释专业概念

        ## 重要提醒
        - 不要一开始就要求用户提供传感器数据，应该先基于农业知识和示例数据回答
        - 可以在回答中提到"如果您有具体的传感器数据，我可以提供更精准的分析"
        - 对于一般性农业咨询，直接给出专业建议，无需依赖特定数据

        你的目标是帮助用户实现农业生产的数字化转型，提高作物产量和品质，降低生产成本和环境风险。
        """
