"""Репозиторий для работы с пользователями в базе данных."""

import re
from contextlib import contextmanager
from typing import List, Optional

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models import User
from app.db.session import SessionLocal
from app.repositories.base_repository import BaseRepository

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


class UserRepository(BaseRepository[User]):
    """Репозиторий для работы с пользователями."""

    def __init__(self, db_session: Optional[Session] = None):
        """Инициализация репозитория."""
        self.db = db_session or SessionLocal()
        self._owns_session = db_session is None
        self._logger = None
        super().__init__(User, self.db)

    def __enter__(self):
        """Вход в context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Выход из context manager."""
        if self._owns_session:
            self.db.close()

    @property
    def logger(self):
        """Логгер для репозитория."""
        if self._logger is None:
            import logging
            self._logger = logging.getLogger(__name__)
        return self._logger

    @contextmanager
    def _transaction(self):
        """Context manager для управления транзакциями."""
        try:
            yield self.db
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Transaction failed: {e}")
            raise

    @staticmethod
    def _validate_email(email: str) -> None:
        """Валидация email адреса."""
        if not email or not email.strip():
            raise ValueError("Email cannot be empty")
        if not EMAIL_REGEX.match(email):
            raise ValueError(f"Invalid email format: {email}")

    @staticmethod
    def _validate_name(name: str) -> None:
        """Валидация имени пользователя."""
        if not name or not name.strip():
            raise ValueError("Name cannot be empty")
        if len(name.strip()) > 100:
            raise ValueError("Name too long (max 100 characters)")

    def add(self, name: str, email: str) -> User:
        """Добавить нового пользователя."""
        self.logger.info(f"Creating user with email: {email}")
        
        self._validate_name(name)
        self._validate_email(email)

        try:
            with self._transaction():
                user = User(name=name.strip(), email=email.strip().lower())
                self.db.add(user)
                self.db.flush()
                self.logger.info(f"User created successfully with id: {user.id}")
                return user
        except IntegrityError as e:
            self.logger.error(f"Failed to create user: email {email} already exists")
            raise ValueError(f"User with email {email} already exists") from e
        except SQLAlchemyError as e:
            self.logger.error(f"Database error while creating user: {e}")
            raise RuntimeError(f"Database error: {e}") from e

    def get_by_id(self, user_id: int) -> Optional[User]:
        """Получить пользователя по ID."""
        self.logger.debug(f"Fetching user by id: {user_id}")
        
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                self.logger.debug(f"User found: id={user.id}, email={user.email}")
            else:
                self.logger.debug(f"User not found: id={user_id}")
            return user
        except SQLAlchemyError as e:
            self.logger.error(f"Database error while fetching user by id {user_id}: {e}")
            raise RuntimeError(f"Database error: {e}") from e

    def get_all(self) -> List[User]:
        """Получить всех пользователей."""
        self.logger.debug("Fetching all users")
        
        try:
            users = self.db.query(User).all()
            self.logger.debug(f"Found {len(users)} users")
            return users
        except SQLAlchemyError as e:
            self.logger.error(f"Database error while fetching all users: {e}")
            raise RuntimeError(f"Database error: {e}") from e

    def close(self):
        """Закрыть сессию базы данных."""
        if self._owns_session:
            self.db.close()
            self.logger.debug("Database session closed")
