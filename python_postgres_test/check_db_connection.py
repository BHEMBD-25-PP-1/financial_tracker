"""Скрипт для проверки подключения к PostgreSQL."""

import sys
from pathlib import Path

# Добавляем родительскую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from python_postgres_test.config import DATABASE_URL
    from python_postgres_test.db import engine
    from sqlalchemy import text
    
    print("Проверка подключения к БД...")
    # Не показываем пароль
    url_parts = DATABASE_URL.split("@")
    if len(url_parts) > 1:
        print(f"URL: {url_parts[0]}@***")
    else:
        print(f"URL: {DATABASE_URL[:50]}...")
    
    # Пытаемся подключиться
    with engine.connect() as connection:
        result = connection.execute(text("SELECT version();"))
        version = result.fetchone()[0]
        print("[OK] PostgreSQL запущен и доступен!")
        print(f"Версия: {version}")
        print("Подключение успешно установлено.")
        
except ImportError as e:
    print(f"[ERROR] Ошибка импорта: {e}")
    print("Убедитесь, что все зависимости установлены: py -m pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] Не удалось подключиться к PostgreSQL")
    print(f"Ошибка: {e}")
    print("\nВозможные причины:")
    print("1. PostgreSQL не запущен")
    print("2. Неверные учетные данные в .env файле")
    print("3. База данных не существует")
    print("4. Порт 5432 недоступен")
    print("\nПроверьте:")
    print("- Создан ли файл .env в python_postgres_test/")
    print("- Правильность учетных данных (DB_USER, DB_PASSWORD, DB_NAME)")
    print("- Существует ли база данных test_db")
    sys.exit(1)

