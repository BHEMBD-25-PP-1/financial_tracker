"""Конфигурация базы данных."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from python_postgres_test.config import DATABASE_URL

# Настройка connection pooling для производительности
engine = create_engine(
    DATABASE_URL,
    pool_size=10,          # Размер пула подключений
    max_overflow=20,       # Максимальное количество дополнительных подключений
    pool_pre_ping=True,    # Проверка соединений перед использованием
    pool_recycle=3600,     # Переподключение через час (предотвращение устаревших соединений)
    echo=False,            # Отключить SQL логирование (включить для отладки)
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
