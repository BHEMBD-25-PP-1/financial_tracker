"""Репозиторий для работы с пользователями.

TODO: Реализовать методы для работы с пользователями в БД
"""

# from typing import Optional
# from sqlalchemy.orm import Session
# from app.db.models import User
# from app.repositories.base_repository import BaseRepository


# class UserRepository(BaseRepository[User]):
#     """Репозиторий для работы с пользователями."""
#
#     def __init__(self, db: Session):
#         """Инициализация репозитория.
#
#         Args:
#             db: Сессия базы данных
#         """
#         super().__init__(User, db)
#
#     def get_by_login(self, login: str) -> Optional[User]:
#         """Получить пользователя по логину.
#
#         Args:
#             login: Логин пользователя
#
#         Returns:
#             Optional[User]: Пользователь или None
#         """
#         return self.db.query(User).filter(User.login == login).first()
#
#     def create_user(
#         self, first_name: str, last_name: str, login: str, password_hash: str
#     ) -> User:
#         """Создать нового пользователя.
#
#         Args:
#             first_name: Имя
#             last_name: Фамилия
#             login: Логин
#             password_hash: Хеш пароля
#
#         Returns:
#             User: Созданный пользователь
#         """
#         user = User(
#             first_name=first_name,
#             last_name=last_name,
#             login=login,
#             password_hash=password_hash,
#         )
#         return self.create(user)

