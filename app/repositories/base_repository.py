"""Базовый репозиторий."""

from typing import Generic, TypeVar, Type, Optional, List
from sqlalchemy.orm import Session

from app.db.base import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseRepository(Generic[ModelType]):
    """Базовый репозиторий с общими методами CRUD."""

    def __init__(self, model: Type[ModelType], db: Session):
        """Инициализация репозитория."""
        self.model = model
        self.db = db

    def get(self, id: int) -> Optional[ModelType]:
        """Получить объект по ID."""
        return self.db.query(self.model).filter(self.model.id == id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Получить список объектов."""
        return self.db.query(self.model).offset(skip).limit(limit).all()

    def create(self, obj: ModelType) -> ModelType:
        """Создать объект."""
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update(self, obj: ModelType) -> ModelType:
        """Обновить объект."""
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, obj: ModelType) -> None:
        """Удалить объект."""
        self.db.delete(obj)
        self.db.commit()
