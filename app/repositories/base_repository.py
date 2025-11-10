"""Базовый репозиторий.

TODO: Реализовать базовый класс репозитория с общими методами CRUD
"""

# from typing import Generic, TypeVar, Type, Optional, List
# from sqlalchemy.orm import Session
# from app.db.base import BaseModel

# ModelType = TypeVar("ModelType", bound=BaseModel)


# class BaseRepository(Generic[ModelType]):
#     """Базовый репозиторий с общими методами CRUD."""
#
#     def __init__(self, model: Type[ModelType], db: Session):
#         """Инициализация репозитория.
#
#         Args:
#             model: Класс модели SQLAlchemy
#             db: Сессия базы данных
#         """
#         self.model = model
#         self.db = db
#
#     def get(self, id: int) -> Optional[ModelType]:
#         """Получить объект по ID.
#
#         Args:
#             id: ID объекта
#
#         Returns:
#             Optional[ModelType]: Объект или None
#         """
#         return self.db.query(self.model).filter(self.model.id == id).first()
#
#     def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
#         """Получить список объектов.
#
#         Args:
#             skip: Количество пропущенных записей
#             limit: Максимальное количество записей
#
#         Returns:
#             List[ModelType]: Список объектов
#         """
#         return self.db.query(self.model).offset(skip).limit(limit).all()
#
#     def create(self, obj: ModelType) -> ModelType:
#         """Создать объект.
#
#         Args:
#             obj: Объект для создания
#
#         Returns:
#             ModelType: Созданный объект
#         """
#         self.db.add(obj)
#         self.db.commit()
#         self.db.refresh(obj)
#         return obj
#
#     def update(self, obj: ModelType) -> ModelType:
#         """Обновить объект.
#
#         Args:
#             obj: Объект для обновления
#
#         Returns:
#             ModelType: Обновленный объект
#         """
#         self.db.commit()
#         self.db.refresh(obj)
#         return obj
#
#     def delete(self, obj: ModelType) -> None:
#         """Удалить объект.
#
#         Args:
#             obj: Объект для удаления
#         """
#         self.db.delete(obj)
#         self.db.commit()

