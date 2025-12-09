"""Контроллеры для Transactions API.

Автоматически сгенерировано из openapi-specs/transactions-service.yaml
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.transactions_repository import TransactionRepository
from app.transactions.models import (
    CreateTransactionRequest,
    Error,
    Transaction,
    TransactionListResponse,
    TransactionType,
    UpdateTransactionRequest,
)

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get(
    "",
    response_model=TransactionListResponse,
    summary="Получить список транзакций",
    description="Получить транзакции с пагинацией и фильтрами",
    operation_id="get_transactions",
)
async def get_transactions(
    page: int = Query(default=1, description="Номер страницы", ge=1),
    size: int = Query(default=20, description="Размер страницы", ge=1, le=100),
    category: Optional[str] = Query(default=None, description="Фильтр по категории"),
    start_date: Optional[date] = Query(
        default=None, description="Дата начала периода (YYYY-MM-DD)"
    ),
    end_date: Optional[date] = Query(
        default=None, description="Дата окончания периода (YYYY-MM-DD)"
    ),
    group_id: Optional[int] = Query(default=None, description="Фильтр по группе"),
    transaction_type: Optional[TransactionType] = Query(
        default=None, description="Фильтр по типу транзакции"
    ),
) -> TransactionListResponse:
    """Получить список транзакций с пагинацией и фильтрами.

    Args:
        page: Номер страницы
        size: Размер страницы
        category: Фильтр по категории
        start_date: Дата начала периода
        end_date: Дата окончания периода
        group_id: Фильтр по группе
        transaction_type: Фильтр по типу транзакции

    Returns:
        TransactionListResponse: Список транзакций с метаданными пагинации
    """
    # TODO: Реализовать логику получения транзакций из базы данных
    # Это заглушка для демонстрации структуры API
    return TransactionListResponse(items=[], total=0, page=page, size=size)


@router.post(
    "",
    response_model=Transaction,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новую транзакцию",
    operation_id="create_transaction",
)
async def create_transaction(
    request: CreateTransactionRequest,
    db: Session = Depends(get_db)
) -> Transaction:
    """Создать новую транзакцию.

    Args:
        request: Данные для создания транзакции
        db: Сессия базы данных

    Returns:
        Transaction: Созданная транзакция
    """
    repo = TransactionRepository(db)
    
    try:
        # TODO: Получить user_id из текущего пользователя (из токена)
        # Пока используем заглушку
        current_user_id = 1  # Заглушка
        
        transaction = repo.create(
            name=request.name,
            type=request.type,
            category=request.category,
            amount=request.amount,
            transaction_date=request.transaction_date,
            user_id=current_user_id,
            group_id=request.group_id
        )
        
        return transaction
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка базы данных при создании транзакции"
        )


@router.get(
    "/{transaction_id}",
    response_model=Transaction,
    summary="Получить транзакцию по ID",
    operation_id="get_transaction_by_id",
)
async def get_transaction_by_id(transaction_id: int) -> Transaction:
    """Получить транзакцию по ID.

    Args:
        transaction_id: ID транзакции

    Returns:
        Transaction: Транзакция

    Raises:
        HTTPException: Если транзакция не найдена
    """
    # TODO: Реализовать логику получения транзакции из базы данных
    # Это заглушка для демонстрации структуры API
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Транзакция с ID {transaction_id} не найдена",
    )


@router.put(
    "/{transaction_id}",
    response_model=Transaction,
    summary="Обновить транзакцию",
    operation_id="update_transaction",
)
async def update_transaction(
    transaction_id: int,
    request: UpdateTransactionRequest,
    db: Session = Depends(get_db)
) -> Transaction:
    """Обновить транзакцию.

    Args:
        transaction_id: ID транзакции
        request: Данные для обновления транзакции
        db: Сессия базы данных

    Returns:
        Transaction: Обновленная транзакция

    Raises:
        HTTPException: Если транзакция не найдена
    """
    repo = TransactionRepository(db)
    
    # TODO: Получить user_id из текущего пользователя (из токена)
    current_user_id = 1  # Заглушка
    
    # Подготавливаем данные для обновления
    update_data = {}
    
    if request.name is not None:
        update_data['name'] = request.name
    
    if request.amount is not None:
        update_data['amount'] = request.amount
    
    if request.category is not None:
        update_data['category'] = request.category
    
    if request.transaction_date is not None:
        update_data['date'] = request.transaction_date
    
    if request.type is not None:
        update_data['type'] = request.type
    
    if request.group_id is not None:
        update_data['group_id'] = request.group_id
    
    try:
        transaction = repo.update(
            transaction_id=transaction_id,
            user_id=current_user_id,
            **update_data
        )
        
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Транзакция с ID {transaction_id} не найдена"
            )
        
        return transaction
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка базы данных при обновлении транзакции"
        )


@router.delete(
    "/{transaction_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить транзакцию",
    operation_id="delete_transaction",
)
async def delete_transaction(transaction_id: int) -> Response:
    """Удалить транзакцию.

    Args:
        transaction_id: ID транзакции

    Returns:
        Response: Пустой ответ со статусом 204

    Raises:
        HTTPException: Если транзакция не найдена
    """
    # TODO: Реализовать логику удаления транзакции из базы данных
    # Это заглушка для демонстрации структуры API
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Транзакция с ID {transaction_id} не найдена",
    )

