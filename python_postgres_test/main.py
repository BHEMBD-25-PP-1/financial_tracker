"""Пример использования UserRepository."""

import logging

from python_postgres_test.logger import setup_logging
from python_postgres_test.user_repository import UserRepository

# Настройка логирования
setup_logging()
logger = logging.getLogger(__name__)

# Использование context manager для автоматического закрытия сессии
with UserRepository() as repo:
    # Создание пользователя
    new_user = repo.add("Иван", "ivan@example.com")
    logger.info(f"Создан: {new_user}")

    # Получение по ID
    user = repo.get_by_id(new_user.id)
    logger.info(f"Найден по ID: {user}")

    # Все пользователи
    all_users = repo.get_all()
    logger.info(f"Все пользователи: {all_users}")

