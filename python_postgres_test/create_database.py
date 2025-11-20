"""Скрипт для создания базы данных test_db."""

import sys
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import psycopg2
    from python_postgres_test.config import DATABASE_URL
    
    # Парсим URL для подключения к системной БД postgres
    url_str = DATABASE_URL.replace('postgresql+psycopg2://', 'postgresql://')
    parsed = urlparse(url_str)
    
    user = parsed.username
    password = parsed.password
    host = parsed.hostname or 'localhost'
    port = parsed.port or 5432
    target_db = parsed.path.lstrip('/') if parsed.path else 'test_db'
    
    print(f"Подключение к PostgreSQL...")
    print(f"Создание базы данных '{target_db}'...")
    
    # Подключаемся к системной БД postgres для создания новой БД
    conn = psycopg2.connect(
        host=host,
        port=int(port),
        user=user,
        password=password,
        database='postgres'
    )
    conn.autocommit = True  # Необходимо для создания БД
    cursor = conn.cursor()
    
    # Проверяем, существует ли база данных
    cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (target_db,))
    exists = cursor.fetchone()
    
    if exists:
        print(f"[INFO] База данных '{target_db}' уже существует")
    else:
        # Создаем базу данных
        cursor.execute(f'CREATE DATABASE "{target_db}";')
        print(f"[OK] База данных '{target_db}' успешно создана!")
    
    cursor.close()
    conn.close()
    
    print("\nТеперь можно запускать:")
    print("  py python_postgres_test/create_tables.py  # Создать таблицы")
    print("  py python_postgres_test/main.py  # Запустить пример")
    
except ImportError as e:
    print(f"[ERROR] Ошибка импорта: {e}")
    sys.exit(1)
except psycopg2.OperationalError as e:
    print(f"[ERROR] Ошибка подключения: {e}")
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] Неожиданная ошибка: {e}")
    sys.exit(1)

