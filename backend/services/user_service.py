# backend/services/user_service.py
from models.user import User
from extensions import db

class UserService:
    @staticmethod
    def get_user_by_id(user_id):
        return User.query.get(user_id)

    @staticmethod
    def create_user(username, password, **kwargs):
        user = User(username=username, password=password, **kwargs)
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def authenticate(username, password):
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            return user
        return None