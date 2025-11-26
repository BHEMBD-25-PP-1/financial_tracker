"""Модуль логирования для проекта."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


class UserIdFilter(logging.Filter):
    """Фильтр для добавления ID пользователя в логи."""

    def filter(self, record):
        """Добавляет user_id в сообщение лога."""
        if hasattr(record, 'user_id'):
            msg = str(record.msg)
            if msg.startswith(f"[user:{record.user_id}]"):
                return True
            record.msg = f"[user:{record.user_id}] {msg}"
        return True


def setup_logging(log_dir: Path = None):
    """Настройка логирования для всего проекта."""
    # Создаем папку для логов
    if log_dir is None:
        log_dir = Path(__file__).parent.parent.parent / "logs"
    else:
        log_dir = Path(log_dir)
    
    log_dir.mkdir(exist_ok=True)

    # Основные настройки
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Формат логов
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Наш кастомный фильтр
    user_filter = UserIdFilter()

    # Файловый обработчик с ротацией
    log_file = log_dir / "app.log"
    file_handler = RotatingFileHandler(
        str(log_file),
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=3,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.addFilter(user_filter)

    # Консольный обработчик
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.addFilter(user_filter)

    # Добавляем обработчики только если их еще нет
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    # Настройка логирования SQLAlchemy (можно отключить в продакшене)
    sqlalchemy_logger = logging.getLogger('sqlalchemy.engine')
    sqlalchemy_logger.setLevel(logging.WARNING)

    return logger

