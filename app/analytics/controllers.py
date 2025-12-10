"""Контроллеры для Analytics API.

Автоматически сгенерировано из openapi-specs/analytics-service.yaml
"""

from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.analytics.models import (
    CategoryAnalyticsResponse,
    CategoryStatistic,
    PeriodAnalyticsResponse,
    PeriodInfo,
    PeriodStatistic,
    PeriodType,
    SummaryResponse,
    TrendDirection,
    TrendInfo,
    TransactionType,
    TrendsResponse,
)
from app.core.dependencies import get_current_user
from app.db.models import User as DBUser
from app.db.session import get_db
from app.repositories.transaction_repository import TransactionRepository

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get(
    "/summary",
    response_model=SummaryResponse,
    summary="Получить общую статистику",
    description="Получение общей статистики по доходам и расходам пользователя",
    operation_id="get_summary",
)
async def get_summary(
    start_date: Optional[date] = Query(
        default=None, description="Дата начала периода (YYYY-MM-DD)"
    ),
    end_date: Optional[date] = Query(
        default=None, description="Дата окончания периода (YYYY-MM-DD)"
    ),
    group_id: Optional[int] = Query(default=None, description="Фильтр по группе (опционально)"),
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> SummaryResponse:
    """Получить общую статистику.

    Args:
        start_date: Дата начала периода
        end_date: Дата окончания периода
        group_id: Фильтр по группе
        current_user: Текущий авторизованный пользователь
        db: Сессия базы данных

    Returns:
        SummaryResponse: Общая статистика
    """
    repo = TransactionRepository(db)
    
    transactions, _ = repo.get_all(
        user_id=current_user.id,
        skip=0,
        limit=10000,
        start_date=start_date,
        end_date=end_date,
        group_id=group_id
    )
    
    total_income = sum(t.amount for t in transactions if t.type.value == "income")
    total_expense = sum(t.amount for t in transactions if t.type.value == "expense")
    balance = total_income - total_expense
    transaction_count = len(transactions)
    
    period = None
    if start_date or end_date:
        period = PeriodInfo(start_date=start_date, end_date=end_date)
    
    return SummaryResponse(
        total_income=total_income,
        total_expense=total_expense,
        balance=balance,
        transaction_count=transaction_count,
        period=period
    )


@router.get(
    "/by-category",
    response_model=CategoryAnalyticsResponse,
    summary="Получить статистику по категориям",
    description="Получение статистики транзакций, сгруппированных по категориям",
    operation_id="get_by_category",
)
async def get_by_category(
    start_date: Optional[date] = Query(
        default=None, description="Дата начала периода (YYYY-MM-DD)"
    ),
    end_date: Optional[date] = Query(
        default=None, description="Дата окончания периода (YYYY-MM-DD)"
    ),
    transaction_type: Optional[TransactionType] = Query(
        default=None, description="Тип транзакций для фильтрации"
    ),
    group_id: Optional[int] = Query(default=None, description="Фильтр по группе (опционально)"),
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> CategoryAnalyticsResponse:
    """Получить статистику по категориям.

    Args:
        start_date: Дата начала периода
        end_date: Дата окончания периода
        transaction_type: Тип транзакций для фильтрации
        group_id: Фильтр по группе
        current_user: Текущий авторизованный пользователь
        db: Сессия базы данных

    Returns:
        CategoryAnalyticsResponse: Статистика по категориям
    """
    repo = TransactionRepository(db)
    
    transactions, _ = repo.get_all(
        user_id=current_user.id,
        skip=0,
        limit=10000,
        start_date=start_date,
        end_date=end_date,
        group_id=group_id,
        transaction_type=transaction_type
    )
    
    # Группируем по категориям
    category_stats = {}
    for t in transactions:
        if t.category not in category_stats:
            category_stats[t.category] = {"total": 0.0, "count": 0, "type": t.type.value}
        category_stats[t.category]["total"] += t.amount
        category_stats[t.category]["count"] += 1
    
    # Вычисляем проценты
    total_amount = sum(stats["total"] for stats in category_stats.values())
    
    categories = [
        CategoryStatistic(
            category=cat,
            total_amount=stats["total"],
            transaction_count=stats["count"],
            percentage=(stats["total"] / total_amount * 100) if total_amount > 0 else 0.0,
            transaction_type=TransactionType(stats["type"])
        )
        for cat, stats in category_stats.items()
    ]
    
    period = None
    if start_date or end_date:
        period = PeriodInfo(start_date=start_date, end_date=end_date)
    
    return CategoryAnalyticsResponse(categories=categories, period=period)


@router.get(
    "/by-period",
    response_model=PeriodAnalyticsResponse,
    summary="Получить статистику по временным периодам",
    description="Получение статистики транзакций, сгруппированных по временным периодам",
    operation_id="get_by_period",
)
async def get_by_period(
    start_date: date = Query(..., description="Дата начала периода (YYYY-MM-DD)"),
    end_date: date = Query(..., description="Дата окончания периода (YYYY-MM-DD)"),
    period_type: PeriodType = Query(
        default=PeriodType.MONTH, description="Тип группировки по времени"
    ),
    group_id: Optional[int] = Query(default=None, description="Фильтр по группе (опционально)"),
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> PeriodAnalyticsResponse:
    """Получить статистику по временным периодам.

    Args:
        start_date: Дата начала периода
        end_date: Дата окончания периода
        period_type: Тип группировки по времени
        group_id: Фильтр по группе
        current_user: Текущий авторизованный пользователь
        db: Сессия базы данных

    Returns:
        PeriodAnalyticsResponse: Статистика по временным периодам

    Raises:
        HTTPException: Если параметры запроса неверные
    """
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Дата начала не может быть позже даты окончания"
        )
    
    repo = TransactionRepository(db)
    
    transactions, _ = repo.get_all(
        user_id=current_user.id,
        skip=0,
        limit=10000,
        start_date=start_date,
        end_date=end_date,
        group_id=group_id
    )
    
    # Группируем по периодам
    period_stats = {}
    
    for t in transactions:
        # Определяем период для транзакции
        if period_type == PeriodType.DAY:
            period_key = t.date.strftime("%Y-%m-%d")
            period_start = t.date
            period_end = t.date
        elif period_type == PeriodType.WEEK:
            # Находим начало недели (понедельник)
            days_since_monday = t.date.weekday()
            period_start = t.date - timedelta(days=days_since_monday)
            period_end = period_start + timedelta(days=6)
            period_key = f"{period_start.strftime('%Y-%m-%d')}"
        elif period_type == PeriodType.MONTH:
            period_key = t.date.strftime("%Y-%m")
            period_start = date(t.date.year, t.date.month, 1)
            # Последний день месяца
            if t.date.month == 12:
                period_end = date(t.date.year + 1, 1, 1) - timedelta(days=1)
            else:
                period_end = date(t.date.year, t.date.month + 1, 1) - timedelta(days=1)
        else:  # YEAR
            period_key = str(t.date.year)
            period_start = date(t.date.year, 1, 1)
            period_end = date(t.date.year, 12, 31)
        
        if period_key not in period_stats:
            period_stats[period_key] = {
                "start": period_start,
                "end": period_end,
                "income": 0.0,
                "expense": 0.0,
                "count": 0
            }
        
        if t.type.value == "income":
            period_stats[period_key]["income"] += t.amount
        else:
            period_stats[period_key]["expense"] += t.amount
        period_stats[period_key]["count"] += 1
    
    periods = [
        PeriodStatistic(
            period=key,
            start_date=stats["start"],
            end_date=stats["end"],
            total_income=stats["income"],
            total_expense=stats["expense"],
            balance=stats["income"] - stats["expense"],
            transaction_count=stats["count"]
        )
        for key, stats in sorted(period_stats.items())
    ]
    
    return PeriodAnalyticsResponse(periods=periods, period_type=period_type)


@router.get(
    "/trends",
    response_model=TrendsResponse,
    summary="Получить тренды доходов и расходов",
    description="Получение информации о трендах доходов и расходов за период",
    operation_id="get_trends",
)
async def get_trends(
    start_date: date = Query(..., description="Дата начала периода (YYYY-MM-DD)"),
    end_date: date = Query(..., description="Дата окончания периода (YYYY-MM-DD)"),
    group_id: Optional[int] = Query(default=None, description="Фильтр по группе (опционально)"),
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> TrendsResponse:
    """Получить тренды доходов и расходов.

    Args:
        start_date: Дата начала периода
        end_date: Дата окончания периода
        group_id: Фильтр по группе
        current_user: Текущий авторизованный пользователь
        db: Сессия базы данных

    Returns:
        TrendsResponse: Тренды доходов и расходов

    Raises:
        HTTPException: Если параметры запроса неверные
    """
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Дата начала не может быть позже даты окончания"
        )
    
    repo = TransactionRepository(db)
    
    # Получаем транзакции за текущий период
    current_transactions, _ = repo.get_all(
        user_id=current_user.id,
        skip=0,
        limit=10000,
        start_date=start_date,
        end_date=end_date,
        group_id=group_id
    )
    
    # Вычисляем длительность периода для сравнения
    period_days = (end_date - start_date).days + 1
    
    # Вычисляем средний период для сравнения (берем предыдущий период такой же длины)
    prev_start = start_date - timedelta(days=period_days)
    prev_end = start_date - timedelta(days=1)
    
    prev_transactions, _ = repo.get_all(
        user_id=current_user.id,
        skip=0,
        limit=10000,
        start_date=prev_start,
        end_date=prev_end,
        group_id=group_id
    )
    
    # Доходы
    current_income = sum(t.amount for t in current_transactions if t.type.value == "income")
    prev_income = sum(t.amount for t in prev_transactions if t.type.value == "income")
    
    income_change = 0.0
    if prev_income > 0:
        income_change = ((current_income - prev_income) / prev_income) * 100
    elif current_income > 0:
        income_change = 100.0
    
    income_direction = TrendDirection.STABLE
    if income_change > 5:
        income_direction = TrendDirection.UP
    elif income_change < -5:
        income_direction = TrendDirection.DOWN
    
    # Расходы
    current_expense = sum(t.amount for t in current_transactions if t.type.value == "expense")
    prev_expense = sum(t.amount for t in prev_transactions if t.type.value == "expense")
    
    expense_change = 0.0
    if prev_expense > 0:
        expense_change = ((current_expense - prev_expense) / prev_expense) * 100
    elif current_expense > 0:
        expense_change = 100.0
    
    expense_direction = TrendDirection.STABLE
    if expense_change > 5:
        expense_direction = TrendDirection.UP
    elif expense_change < -5:
        expense_direction = TrendDirection.DOWN
    
    period = PeriodInfo(start_date=start_date, end_date=end_date)
    
    return TrendsResponse(
        income_trend=TrendInfo(
            direction=income_direction,
            change_percentage=income_change,
            average_daily=current_income / period_days if period_days > 0 else 0.0
        ),
        expense_trend=TrendInfo(
            direction=expense_direction,
            change_percentage=expense_change,
            average_daily=current_expense / period_days if period_days > 0 else 0.0
        ),
        period=period
    )

