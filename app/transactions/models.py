"""Модели данных для Transactions API.

Автоматически сгенерировано из openapi-specs/transactions-service.yaml
"""

from datetime import date as dt_date, datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class TransactionType(str, Enum):
    """Тип транзакции."""

    INCOME = "income"
    EXPENSE = "expense"


class TransactionCategory(str, Enum):
    """Категория транзакции."""

    PRODUCTS = "Продукты"
    CLOTHING_AND_SHOES = "Одежда и обувь"
    HOME_AND_REPAIR = "Дом и ремонт"
    HOUSING = "Жилье"
    EDUCATION = "Образование"
    WORK = "Работа"
    FOOD = "Еда"
    LEISURE = "Досуг"
    SHOPPING = "Покупки"
    TRAVEL = "Путешествия"
    TRANSPORT = "Транспорт"
    TRANSFERS = "Переводы"
    COSMETICS_AND_HOUSEHOLD = "Косметика и бытовая химия"
    SPORTS = "Спорт"
    ENTERTAINMENT = "Развлечения"
    CAFE_AND_RESTAURANTS = "Кафе и рестораны"


class Transaction(BaseModel):
    """Модель транзакции."""

    id: int
    name: str
    type: TransactionType
    category: TransactionCategory
    amount: float
    date: dt_date
    user_id: int
    group_id: Optional[int] = Field(None, description="ID группы, если транзакция относится к группе")
    created_at: datetime
    updated_at: datetime

    class Config:
        """Конфигурация модели."""

        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Покупка продуктов",
                "type": "expense",
                "category": "Продукты",
                "amount": 1500.50,
                "date": "2024-01-15",
                "user_id": 1,
                "group_id": None,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
            }
        }


class CreateTransactionRequest(BaseModel):
    """Запрос на создание транзакции."""

    name: str
    type: TransactionType
    category: TransactionCategory
    amount: float
    date: dt_date
    group_id: Optional[int] = Field(None, description="ID группы, если транзакция относится к группе")

    class Config:
        """Конфигурация модели."""

        json_schema_extra = {
            "example": {
                "name": "Покупка продуктов",
                "type": "expense",
                "category": "Продукты",
                "amount": 1500.50,
                "date": "2024-01-15",
                "group_id": None,
            }
        }


class UpdateTransactionRequest(BaseModel):
    """Запрос на обновление транзакции."""

    name: Optional[str] = None
    type: Optional[TransactionType] = None
    category: Optional[TransactionCategory] = None
    amount: Optional[float] = None
    # Дата как optional date (null или YYYY-MM-DD)
    date: Optional[dt_date] = None
    group_id: Optional[int] = Field(None, description="ID группы, если транзакция относится к группе")

    class Config:
        """Конфигурация модели."""

        json_schema_extra = {
            "example": {
                "name": "Покупка продуктов",
                "type": "expense",
                "category": "Продукты",
                "amount": 1500.50,
                "date": "2024-01-15",
                "group_id": None,
            }
        }


class TransactionListResponse(BaseModel):
    """Ответ со списком транзакций."""

    items: List[Transaction]
    total: int
    page: int
    size: int

    class Config:
        """Конфигурация модели."""

        json_schema_extra = {
            "example": {
                "items": [],
                "total": 0,
                "page": 1,
                "size": 20,
            }
        }


class Error(BaseModel):
    """Модель ошибки."""

    detail: str
    error_code: Optional[str] = None

    class Config:
        """Конфигурация модели."""

        json_schema_extra = {
            "example": {
                "detail": "Описание ошибки",
                "error_code": "VALIDATION_ERROR",
            }
        }

