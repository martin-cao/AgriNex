# backend/services/forecast_service.py
from backend.models.prediction import Prediction
from backend.extensions import db

class ForecastService:
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