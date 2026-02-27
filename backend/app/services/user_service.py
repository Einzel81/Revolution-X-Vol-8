from sqlalchemy.orm import Session
from app.auth.models import User
from app.auth.schemas import UserCreate

class UserService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_by_id(self, user_id: str):
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_email(self, email: str):
        return self.db.query(User).filter(User.email == email).first()
    
    def create_user(self, user_data: UserCreate):
        from app.auth.service import AuthService
        auth_service = AuthService(self.db)
        return auth_service.register(user_data)
    
    def update_user(self, user_id: str, **kwargs):
        user = self.get_user_by_id(user_id)
        if user:
            for key, value in kwargs.items():
                setattr(user, key, value)
            self.db.commit()
            self.db.refresh(user)
        return user
    
    def delete_user(self, user_id: str):
        user = self.get_user_by_id(user_id)
        if user:
            self.db.delete(user)
            self.db.commit()
        return user
