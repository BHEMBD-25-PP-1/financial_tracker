from entity import User
from db import SessionLocal

class UserRepository:
    def __init__(self):
        self.db = SessionLocal()

    def add(self, name: str, email: str) -> User:
        user = User(name=name, email=email)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_by_id(self, user_id: int):
        return self.db.query(User).filter(User.id == user_id).first()

    def get_all(self):
        return self.db.query(User).all()

