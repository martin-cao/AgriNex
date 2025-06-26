# backend/services/forecast_service.py
from backend.models.reading import Reading
from backend.models.prediction import Prediction
from backend.extensions import db
from prophet import Prophet
import pandas as pd

class ForecastService:
    @staticmethod
    def get_numeric_fields():
        # 自动识别 readings 表中的数值型字段
        return [
            col.name for col in Reading.__table__.columns
            if str(col.type) in ['FLOAT', 'INTEGER', 'REAL', 'NUMERIC']
            and col.name not in ['reading_id', 'device_id', 'timestamp']
        ]

    @staticmethod
    def get_history(device_id, field, limit=200):
        # 获取历史数据
        query = Reading.query.filter_by(device_id=device_id).order_by(Reading.timestamp.desc()).limit(limit)
        df = pd.DataFrame([
            {'ds': r.timestamp, 'y': getattr(r, field)}
            for r in query if getattr(r, field) is not None
        ])
        return df

    @staticmethod
    def predict(device_id, field, periods=24, freq='H'):
        df = ForecastService.get_history(device_id, field)
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
    def save_predictions(device_id, field, forecast_list):
        for item in forecast_list:
            prediction = Prediction(
                device_id=device_id,
                predict_ts=item['timestamp'],
                yhat=item['yhat'],
                yhat_lower=item['yhat_lower'],
                yhat_upper=item['yhat_upper']
            )
            db.session.add(prediction)
        db.session.commit()

    @staticmethod
    def save_prediction(device_id, predict_ts, yhat, yhat_lower, yhat_upper):
        prediction = Prediction(
            device_id=device_id,
            predict_ts=predict_ts,
            yhat=yhat,
            yhat_lower=yhat_lower,
            yhat_upper=yhat_upper
        )
        db.session.add(prediction)
        db.session.commit()
        return prediction

    @staticmethod
    def get_predictions(device_id, limit=10):
        return Prediction.query.filter_by(device_id=device_id).order_by(Prediction.predict_ts.desc()).limit(limit).all()