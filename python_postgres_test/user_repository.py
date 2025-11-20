# user_repository.py
from sqlalchemy.orm import Session
from user import User  # импорт вашей сущности User

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user: User):
        # Проверяем, существует ли пользователь с таким email
        existing_user = self.db.query(User).filter(User.email == user.email).first()
        if existing_user:
            print(f"Пользователь с email {user.email} уже существует. ID: {existing_user.id}")
            return existing_user

        # Если нет, создаём нового
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_by_id(self, user_id: int):
        return self.db.query(User).filter(User.id == user_id).first()

