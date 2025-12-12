"""Скрипт для запуска миграций Alembic."""

import sys
import os

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(__file__))

try:
    from alembic.config import Config
    from alembic import command
    
    if __name__ == "__main__":
        alembic_cfg = Config("alembic.ini")
        print("Применяю миграции...")
        command.upgrade(alembic_cfg, "head")
        print("Миграции успешно применены!")
except ImportError as e:
    print(f"Ошибка импорта: {e}")
    print("Убедитесь, что alembic установлен: pip install alembic")
    sys.exit(1)
except Exception as e:
    print(f"Ошибка при применении миграций: {e}")
    sys.exit(1)

