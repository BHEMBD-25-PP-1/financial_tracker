"""Репозиторий для работы с пользователями в базе данных."""

import re
from contextlib import contextmanager
from typing import List, Optional

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models import User
from app.db.session import SessionLocal
from app.repositories.base_repository import BaseRepository
from app.core.security import get_password_hash, verify_password

LOGIN_REGEX = re.compile(r'^[a-zA-Z0-9_]+$')


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
    def _validate_login(login: str) -> None:
        """Валидация логина."""
        if not login or not login.strip():
            raise ValueError("Login cannot be empty")
        if len(login.strip()) < 3:
            raise ValueError("Login too short (min 3 characters)")
        if len(login.strip()) > 50:
            raise ValueError("Login too long (max 50 characters)")
        if not LOGIN_REGEX.match(login):
            raise ValueError("Login can only contain letters, numbers and underscores")

    @staticmethod
    def _validate_name(name: str, field_name: str = "Name") -> None:
        """Валидация имени пользователя."""
        if not name or not name.strip():
            raise ValueError(f"{field_name} cannot be empty")
        if len(name.strip()) > 100:
            raise ValueError(f"{field_name} too long (max 100 characters)")

    def add(
        self,
        first_name: str,
        last_name: str,
        login: str,
        password: str
    ) -> User:
        """Добавить нового пользователя."""
        self.logger.info(f"Creating user with login: {login}")
        
        self._validate_name(first_name, "First name")
        self._validate_name(last_name, "Last name")
        self._validate_login(login)

        if not password or len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")

        try:
            with self._transaction():
                password_hash = get_password_hash(password)
                user = User(
                    first_name=first_name.strip(),
                    last_name=last_name.strip(),
                    login=login.strip().lower(),
                    password_hash=password_hash
                )
                self.db.add(user)
                self.db.flush()
                self.logger.info(f"User created successfully with id: {user.id}")
                return user
        except IntegrityError as e:
            self.logger.error(f"Failed to create user: login {login} already exists")
            raise ValueError(f"User with login {login} already exists") from e
        except SQLAlchemyError as e:
            self.logger.error(f"Database error while creating user: {e}")
            raise RuntimeError(f"Database error: {e}") from e

    def get_by_login(self, login: str) -> Optional[User]:
        """Получить пользователя по логину."""
        self.logger.debug(f"Fetching user by login: {login}")
        
        try:
            user = self.db.query(User).filter(User.login == login.lower().strip()).first()
            if user:
                self.logger.debug(f"User found: id={user.id}, login={user.login}")
            else:
                self.logger.debug(f"User not found: login={login}")
            return user
        except SQLAlchemyError as e:
            self.logger.error(f"Database error while fetching user by login {login}: {e}")
            raise RuntimeError(f"Database error: {e}") from e

    def verify_user(self, login: str, password: str) -> Optional[User]:
        """Проверить учетные данные пользователя."""
        user = self.get_by_login(login)
        if user and verify_password(password, user.password_hash):
            return user
        return None

    def update_password(self, user_id: int, new_password: str) -> bool:
        """Обновить пароль пользователя."""
        if not new_password or len(new_password) < 8:
            raise ValueError("Password must be at least 8 characters long")

        user = self.get_by_id(user_id)
        if not user:
            return False

        try:
            with self._transaction():
                user.password_hash = get_password_hash(new_password)
                self.db.flush()
                self.logger.info(f"Password updated for user id: {user_id}")
                return True
        except SQLAlchemyError as e:
            self.logger.error(f"Database error while updating password: {e}")
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
