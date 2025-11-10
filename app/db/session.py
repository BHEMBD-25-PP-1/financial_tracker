"""Конфигурация сессий базы данных.

TODO: Реализовать создание сессий для работы с БД
"""

# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker, Session
# from typing import Generator

# from app.core.config import settings

# engine = create_engine(settings.DATABASE_URL)
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# def get_db() -> Generator[Session, None, None]:
#     """Получить сессию базы данных.
#
#     Yields:
#         Session: Сессия базы данных
#     """
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

