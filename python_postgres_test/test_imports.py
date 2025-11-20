"""Тестовый скрипт для проверки импортов."""

import sys
from pathlib import Path

# Добавляем родительскую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from python_postgres_test.config import DATABASE_URL
    print("✓ config.py - OK")
except Exception as e:
    print(f"✗ config.py - ERROR: {e}")
    sys.exit(1)

try:
    from python_postgres_test.db import engine, SessionLocal
    print("✓ db.py - OK")
except Exception as e:
    print(f"✗ db.py - ERROR: {e}")
    sys.exit(1)

try:
    from python_postgres_test.entity import Base, User
    print("✓ entity.py - OK")
except Exception as e:
    print(f"✗ entity.py - ERROR: {e}")
    sys.exit(1)

try:
    from python_postgres_test.logger import setup_logging, UserIdFilter
    print("✓ logger.py - OK")
except Exception as e:
    print(f"✗ logger.py - ERROR: {e}")
    sys.exit(1)

try:
    from python_postgres_test.user_repository import UserRepository
    print("✓ user_repository.py - OK")
except Exception as e:
    print(f"✗ user_repository.py - ERROR: {e}")
    sys.exit(1)

try:
    from python_postgres_test import DATABASE_URL, Base, User, engine, SessionLocal, UserRepository
    print("✓ __init__.py - OK")
except Exception as e:
    print(f"✗ __init__.py - ERROR: {e}")
    sys.exit(1)

print("\nВсе импорты успешны! ✓")

