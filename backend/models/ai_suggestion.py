from backend.extensions import db
from datetime import datetime

class AISuggestion(db.Model):
    __tablename__ = 'ai_suggestions'
    
    id = db.Column(db.Integer, primary_key=True)
    sensor_id = db.Column(db.Integer, db.ForeignKey('sensors.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    prompt = db.Column(db.Text)
    suggestion = db.Column(db.Text)
    model_used = db.Column(db.String(50), default='gpt-4o')
    tokens_used = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    sensor = db.relationship('Sensor', backref=db.backref('ai_suggestions', lazy=True))
    user = db.relationship('User', backref=db.backref('ai_suggestions', lazy=True))
    
    def to_dict(self):
        return {
            'id': self.id,
            'sensor_id': self.sensor_id,
            'user_id': self.user_id,
            'prompt': self.prompt,
            'suggestion': self.suggestion,
            'model_used': self.model_used,
            'tokens_used': self.tokens_used,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def create_suggestion(cls, user_id, prompt, suggestion, sensor_id=None, 
                         model_used='gpt-4o', tokens_used=0):
        """创建AI建议记录"""
        suggestion_record = cls(
            user_id=user_id,
            sensor_id=sensor_id,
            prompt=prompt,
            suggestion=suggestion,
            model_used=model_used,
            tokens_used=tokens_used
        )
        db.session.add(suggestion_record)
        return suggestion_record
