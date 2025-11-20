"""Простая проверка подключения к PostgreSQL."""

import sys
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import psycopg2
    from python_postgres_test.config import DATABASE_URL
    
    # Парсим URL для получения параметров
    url_str = DATABASE_URL.replace('postgresql+psycopg2://', 'postgresql://')
    parsed = urlparse(url_str)
    
    user = parsed.username
    password = parsed.password
    host = parsed.hostname or 'localhost'
    port = parsed.port or 5432
    database = parsed.path.lstrip('/') if parsed.path else 'postgres'
    
    print(f"Попытка подключения:")
    print(f"  Host: {host}")
    print(f"  Port: {port}")
    print(f"  User: {user}")
    print(f"  Database: {database}")
    
    # Пробуем подключиться к postgres (системная БД)
    try:
        conn = psycopg2.connect(
            host=host,
            port=int(port),
            user=user,
            password=password,
            database='postgres'  # Подключаемся к системной БД
        )
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"\n[OK] Подключение к PostgreSQL успешно!")
        print(f"Версия: {version}")
        cursor.close()
        conn.close()
        
        # Теперь проверяем, существует ли test_db
        conn = psycopg2.connect(
            host=host,
            port=int(port),
            user=user,
            password=password,
            database='postgres'
        )
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (database,))
        exists = cursor.fetchone()
        if exists:
            print(f"\n[OK] База данных '{database}' существует")
        else:
            print(f"\n[WARNING] База данных '{database}' не существует")
            print(f"Создайте ее командой: CREATE DATABASE {database};")
        cursor.close()
        conn.close()
        
    except psycopg2.OperationalError as e:
        print(f"\n[ERROR] Ошибка подключения: {e}")
        print("\nПроверьте:")
        print("1. Правильность пароля для пользователя postgres")
        print("2. Что PostgreSQL запущен")
        print("3. Что пользователь postgres существует и имеет права")
        
except ImportError as e:
    print(f"[ERROR] Ошибка импорта: {e}")
except Exception as e:
    print(f"[ERROR] Неожиданная ошибка: {e}")
