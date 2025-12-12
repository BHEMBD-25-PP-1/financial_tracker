"""Контроллеры для Transactions API.

Автоматически сгенерировано из openapi-specs/transactions-service.yaml
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.models import User as DBUser
from app.db.session import get_db
from app.transactions.service import TransactionService
from app.transactions.models import (
    CreateTransactionRequest,
    Transaction,
    TransactionListResponse,
    TransactionType,
    TransactionCategory,
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
    category: Optional[TransactionCategory] = Query(default=None, description="Фильтр по категории"),
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
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
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
        current_user: Текущий авторизованный пользователь
        db: Сессия базы данных

    Returns:
        TransactionListResponse: Список транзакций с метаданными пагинации
    """
    try:
        service = TransactionService(db)
        
        transaction_items, total = service.get_transactions(
            user_id=current_user.id,
            page=page,
            size=size,
            category=category,
            start_date=start_date,
            end_date=end_date,
            group_id=group_id,
            transaction_type=transaction_type
        )
        
        return TransactionListResponse(
            items=transaction_items,
            total=total,
            page=page,
            size=size
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении транзакций: {str(e)}"
        )


@router.post(
    "",
    response_model=Transaction,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новую транзакцию",
    operation_id="create_transaction",
)
async def create_transaction(
    request: CreateTransactionRequest,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Transaction:
    """Создать новую транзакцию.

    Args:
        request: Данные для создания транзакции
        current_user: Текущий авторизованный пользователь
        db: Сессия базы данных

    Returns:
        Transaction: Созданная транзакция
    """
    service = TransactionService(db)
    
    try:
        transaction = service.create_transaction(
            name=request.name,
            transaction_type=request.type,
            category=request.category,
            amount=request.amount,
            transaction_date=request.date,
            user_id=current_user.id,
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
            detail=f"Ошибка базы данных при создании транзакции: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при создании транзакции: {str(e)}"
        )


@router.get(
    "/{transaction_id}",
    response_model=Transaction,
    summary="Получить транзакцию по ID",
    operation_id="get_transaction_by_id",
)
async def get_transaction_by_id(
    transaction_id: int,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Transaction:
    """Получить транзакцию по ID.

    Args:
        transaction_id: ID транзакции
        current_user: Текущий авторизованный пользователь
        db: Сессия базы данных

    Returns:
        Transaction: Транзакция

    Raises:
        HTTPException: Если транзакция не найдена
    """
    service = TransactionService(db)
    
    transaction = service.get_transaction_by_id(transaction_id, current_user.id)
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Транзакция с ID {transaction_id} не найдена",
        )
    
    return transaction


@router.put(
    "/{transaction_id}",
    response_model=Transaction,
    summary="Обновить транзакцию",
    operation_id="update_transaction",
)
async def update_transaction(
    transaction_id: int,
    request: UpdateTransactionRequest,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Transaction:
    """Обновить транзакцию.

    Args:
        transaction_id: ID транзакции
        request: Данные для обновления транзакции
        current_user: Текущий авторизованный пользователь
        db: Сессия базы данных

    Returns:
        Transaction: Обновленная транзакция

    Raises:
        HTTPException: Если транзакция не найдена
    """
    service = TransactionService(db)
    
    try:
        transaction = service.update_transaction(
            transaction_id=transaction_id,
            user_id=current_user.id,
            name=request.name,
            amount=request.amount,
            category=request.category,
            date=request.date,
            transaction_type=request.type,
            group_id=request.group_id
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
    except RuntimeError:
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
async def delete_transaction(
    transaction_id: int,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Response:
    """Удалить транзакцию.

    Args:
        transaction_id: ID транзакции
        current_user: Текущий авторизованный пользователь
        db: Сессия базы данных

    Returns:
        Response: Пустой ответ со статусом 204

    Raises:
        HTTPException: Если транзакция не найдена
    """
    service = TransactionService(db)
    
    try:
        deleted = service.delete_transaction(transaction_id, current_user.id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Транзакция с ID {transaction_id} не найдена",
            )
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка базы данных при удалении транзакции"
        )

