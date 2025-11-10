"""Модели данных для Analytics API.

Автоматически сгенерировано из openapi-specs/analytics-service.yaml
"""

from datetime import date
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class TransactionType(str, Enum):
    """Тип транзакции."""

    INCOME = "income"
    EXPENSE = "expense"


class PeriodType(str, Enum):
    """Тип временного периода."""

    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


class TrendDirection(str, Enum):
    """Направление тренда."""

    UP = "up"
    DOWN = "down"
    STABLE = "stable"


class PeriodInfo(BaseModel):
    """Информация о периоде."""

    start_date: Optional[date] = None
    end_date: Optional[date] = None


class SummaryResponse(BaseModel):
    """Общая статистика."""

    total_income: float
    total_expense: float
    balance: float
    transaction_count: int
    period: Optional[PeriodInfo] = None

    class Config:
        """Конфигурация модели."""

        json_schema_extra = {
            "example": {
                "total_income": 100000.00,
                "total_expense": 75000.00,
                "balance": 25000.00,
                "transaction_count": 150,
            }
        }


class CategoryStatistic(BaseModel):
    """Статистика по категории."""

    category: str
    total_amount: float
    transaction_count: int
    percentage: Optional[float] = None
    transaction_type: Optional[TransactionType] = None

    class Config:
        """Конфигурация модели."""

        json_schema_extra = {
            "example": {
                "category": "Еда",
                "total_amount": 25000.00,
                "transaction_count": 45,
                "percentage": 33.33,
                "transaction_type": "expense",
            }
        }


class CategoryAnalyticsResponse(BaseModel):
    """Ответ со статистикой по категориям."""

    categories: List[CategoryStatistic]
    period: Optional[PeriodInfo] = None

    class Config:
        """Конфигурация модели."""

        json_schema_extra = {
            "example": {
                "categories": [],
            }
        }


class PeriodStatistic(BaseModel):
    """Статистика за период."""

    period: str
    start_date: date
    end_date: date
    total_income: float
    total_expense: float
    balance: float
    transaction_count: int

    class Config:
        """Конфигурация модели."""

        json_schema_extra = {
            "example": {
                "period": "2024-01",
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
                "total_income": 50000.00,
                "total_expense": 30000.00,
                "balance": 20000.00,
                "transaction_count": 75,
            }
        }


class PeriodAnalyticsResponse(BaseModel):
    """Ответ со статистикой по временным периодам."""

    periods: List[PeriodStatistic]
    period_type: PeriodType

    class Config:
        """Конфигурация модели."""

        json_schema_extra = {
            "example": {
                "periods": [],
                "period_type": "month",
            }
        }


class TrendInfo(BaseModel):
    """Информация о тренде."""

    direction: TrendDirection
    change_percentage: float
    average_daily: float

    class Config:
        """Конфигурация модели."""

        json_schema_extra = {
            "example": {
                "direction": "up",
                "change_percentage": 15.5,
                "average_daily": 3333.33,
            }
        }


class TrendsResponse(BaseModel):
    """Ответ с трендами."""

    income_trend: TrendInfo
    expense_trend: TrendInfo
    period: Optional[PeriodInfo] = None

    class Config:
        """Конфигурация модели."""

        json_schema_extra = {
            "example": {
                "income_trend": {
                    "direction": "up",
                    "change_percentage": 15.5,
                    "average_daily": 3333.33,
                },
                "expense_trend": {
                    "direction": "down",
                    "change_percentage": -5.2,
                    "average_daily": 2500.00,
                },
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

