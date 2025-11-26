"""Конфигурация приложения."""

import os
from pathlib import Path
from urllib.parse import quote_plus

# Загрузка переменных окружения из .env файла (если установлен python-dotenv)
try:
    from dotenv import load_dotenv
    # Загружаем .env из корня проекта
    env_path = Path(__file__).parent.parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)
except ImportError:
    pass

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"postgresql+psycopg2://{quote_plus(os.getenv('DB_USER', 'postgres'))}:{quote_plus(os.getenv('DB_PASSWORD', ''))}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME', 'financial_tracker')}"
)

