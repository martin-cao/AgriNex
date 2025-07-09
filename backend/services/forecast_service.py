# backend/services/forecast_service.py
from models.reading import Reading
from models.prediction import Prediction
from extensions import db
from prophet import Prophet
import pandas as pd

class ForecastService:
    @staticmethod
    def get_numeric_fields():
        """
        获取 Reading 模型中的数值型字段
        Review 建议2修复：使用更可靠的类型检查
        """
        # 基于实际模型定义的已知数值字段
        known_numeric_fields = ['numeric_value']
        
        # 动态检查其他可能的数值字段（可选增强）
        try:
            additional_fields = []
            for col in Reading.__table__.columns:
                col_type_str = str(col.type).upper()
                # 改进的类型检查：更详细的类型匹配
                is_numeric = any(type_name in col_type_str for type_name in [
                    'FLOAT', 'INTEGER', 'REAL', 'NUMERIC', 'DOUBLE', 'DECIMAL'
                ])
                
                if (is_numeric 
                    and col.name not in ['id', 'sensor_id', 'timestamp'] 
                    and col.name not in known_numeric_fields):
                    additional_fields.append(col.name)
            
            return known_numeric_fields + additional_fields
            
        except Exception:
            # 如果动态检查失败，返回已知字段
            return known_numeric_fields

    @staticmethod
    def get_history(sensor_id, field='numeric_value', limit=200):
        """获取传感器历史数据"""
        query = Reading.query.filter_by(sensor_id=sensor_id).order_by(Reading.timestamp.desc()).limit(limit)
        df = pd.DataFrame([
            {'ds': r.timestamp, 'y': getattr(r, field)}
            for r in query if getattr(r, field) is not None
        ])
        return df

    @staticmethod
    def get_history_by_device(device_id, field='numeric_value', limit=200):
        """
        通过设备ID获取历史数据（聚合所有传感器）
        用于支持设备级别的预测API
        """
        from models.sensor import Sensor
        
        # 获取设备下的所有传感器
        sensors = Sensor.query.filter_by(device_id=device_id).all()
        if not sensors:
            return pd.DataFrame()
        
        # 聚合所有传感器的数据
        all_data = []
        for sensor in sensors:
            query = Reading.query.filter_by(sensor_id=sensor.id).order_by(Reading.timestamp.desc()).limit(limit)
            for r in query:
                if getattr(r, field) is not None:
                    all_data.append({'ds': r.timestamp, 'y': getattr(r, field)})
        
        df = pd.DataFrame(all_data)
        return df.drop_duplicates().sort_values('ds') if not df.empty else df

    @staticmethod
    def predict(sensor_id, field='numeric_value', periods=24, freq='H'):
        """传感器级别预测"""
        df = ForecastService.get_history(sensor_id, field)
        if df.empty or len(df) < 10:
            return None, "历史数据不足，无法预测"
        df = df.sort_values('ds')
        model = Prophet()
        model.fit(df)
        future = model.make_future_dataframe(periods=periods, freq=freq)
        forecast = model.predict(future)
        # 只返回未来的预测
        forecast = forecast.tail(periods)
        result = [
            {
                'timestamp': row['ds'].isoformat(),
                'yhat': row['yhat'],
                'yhat_lower': row['yhat_lower'],
                'yhat_upper': row['yhat_upper']
            }
            for _, row in forecast.iterrows()
        ]
        return result, None

    @staticmethod
    def predict_by_device(device_id, field='numeric_value', periods=24, freq='H'):
        """
        设备级别预测（聚合设备下所有传感器数据）
        用于支持现有的设备预测API
        """
        df = ForecastService.get_history_by_device(device_id, field)
        if df.empty or len(df) < 10:
            return None, "设备历史数据不足，无法预测"
        df = df.sort_values('ds')
        model = Prophet()
        model.fit(df)
        future = model.make_future_dataframe(periods=periods, freq=freq)
        forecast = model.predict(future)
        # 只返回未来的预测
        forecast = forecast.tail(periods)
        result = [
            {
                'timestamp': row['ds'].isoformat(),
                'yhat': row['yhat'],
                'yhat_lower': row['yhat_lower'],
                'yhat_upper': row['yhat_upper']
            }
            for _, row in forecast.iterrows()
        ]
        return result, None

    @staticmethod
    def save_predictions(sensor_id, field, forecast_list):
        """
        保存预测结果到数据库
        Review 建议1修复：使用正确的 sensor_id 字段
        """
        for item in forecast_list:
            # 处理 timestamp 字符串转换
            if isinstance(item['timestamp'], str):
                from datetime import datetime
                predict_ts = datetime.fromisoformat(item['timestamp'].replace('Z', '+00:00'))
            else:
                predict_ts = item['timestamp']
            
            prediction = Prediction(
                sensor_id=sensor_id,
                predict_ts=predict_ts,
                yhat=item['yhat'],
                yhat_lower=item['yhat_lower'],
                yhat_upper=item['yhat_upper'],
                metric_type=field
            )
            db.session.add(prediction)
        db.session.commit()

    @staticmethod
    def save_prediction(sensor_id, predict_ts, yhat, yhat_lower, yhat_upper, metric_type=None):
        """
        保存单个预测结果
        Review 建议1修复：使用正确的 sensor_id 字段
        """
        prediction = Prediction(
            sensor_id=sensor_id,
            predict_ts=predict_ts,
            yhat=yhat,
            yhat_lower=yhat_lower,
            yhat_upper=yhat_upper,
            metric_type=metric_type
        )
        db.session.add(prediction)
        db.session.commit()
        return prediction

    @staticmethod
    def get_predictions(sensor_id, limit=10):
        """
        获取传感器的预测结果
        Review 建议1修复：使用正确的 sensor_id 字段
        """
        return Prediction.query.filter_by(sensor_id=sensor_id).order_by(Prediction.predict_ts.desc()).limit(limit).all()