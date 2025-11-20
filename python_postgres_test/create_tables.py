"""Скрипт для создания таблиц в базе данных."""

from python_postgres_test.db import engine
from python_postgres_test.entity import Base

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print("Таблицы созданы")
