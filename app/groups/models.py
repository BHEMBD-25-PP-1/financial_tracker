"""Модели данных для Groups API.

Автоматически сгенерировано из openapi-specs/groups-service.yaml
"""

from datetime import date, datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class GroupRole(str, Enum):
    """Роль участника группы."""

    owner = "owner"
    member = "member"


class Group(BaseModel):
    """Модель группы."""

    id: int
    name: str
    owner_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "Семья Ивановых",
                "owner_id": 1,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
            }
        }
    )


class CreateGroupRequest(BaseModel):
    """Запрос на создание группы."""

    owner_id: int = Field(..., example=1)
    name: str = Field(..., min_length=1, max_length=200, examples=["Семья Ивановых"])
      
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Семья Ивановых",
                "owner_id": 1,
            }
        }
    )


class UpdateGroupRequest(BaseModel):
    """Запрос на обновление группы."""

    name: str = Field(..., min_length=1, max_length=200, examples=["Семья Ивановых"])

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Семья Ивановых",
            }
        }
    )


class GroupListResponse(BaseModel):
    """Ответ со списком групп."""

    items: List[Group]
    total: int
    page: int
    size: int

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [],
                "total": 0,
                "page": 1,
                "size": 20,
            }
        }
    )


class UserInfo(BaseModel):
    """Информация о пользователе."""

    id: int
    first_name: str
    last_name: str
    login: str


class GroupMember(BaseModel):
    """Модель участника группы."""

    id: int
    user_id: int
    group_id: int
    role: GroupRole
    joined_at: datetime
    user: Optional[UserInfo] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "user_id": 2,
                "group_id": 1,
                "role": "member",
                "joined_at": "2024-01-15T10:30:00Z",
            }
        }
    )


class GroupMembersResponse(BaseModel):
    """Ответ со списком участников группы."""

    members: List[GroupMember]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "members": [],
            }
        }
    )


class AddMemberRequest(BaseModel):
    """Запрос на добавление участника в группу."""

    user_id: int = Field(..., examples=[2])

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": 2,
            }
        }
    )


class CategoryStatistic(BaseModel):
    """Статистика по категории."""

    category: str
    total_amount: float
    transaction_count: int


class PeriodInfo(BaseModel):
    """Информация о периоде."""

    start_date: Optional[date] = None
    end_date: Optional[date] = None


class GroupAnalyticsResponse(BaseModel):
    """Ответ с аналитикой по группе."""

    group_id: int
    total_income: float
    total_expense: float
    balance: float
    statistics: List[CategoryStatistic]
    period: Optional[PeriodInfo] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "group_id": 1,
                "total_income": 50000.00,
                "total_expense": 30000.00,
                "balance": 20000.00,
                "statistics": [],
            }
        }
    )


class Error(BaseModel):
    """Модель ошибки."""

    detail: str
    error_code: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "detail": "Описание ошибки",
                "error_code": "VALIDATION_ERROR",
            }
        }
    )
