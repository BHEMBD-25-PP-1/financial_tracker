"""ORM модели для базы данных."""

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class User(Base):
    """Модель пользователя."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)

    def __repr__(self):
        """Строковое представление объекта."""
        return f"<User id={self.id} name='{self.name}' email='{self.email}'>"
