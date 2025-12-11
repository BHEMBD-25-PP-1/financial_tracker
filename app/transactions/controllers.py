"""Контроллеры для Transactions API.

Автоматически сгенерировано из openapi-specs/transactions-service.yaml
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.models import User as DBUser
from app.db.session import get_db
from app.repositories.transaction_repository import TransactionRepository
from app.transactions.models import (
    CreateTransactionRequest,
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
    repo = TransactionRepository(db)
    
    skip = (page - 1) * size
    
    transactions, total = repo.get_all(
        user_id=current_user.id,
        skip=skip,
        limit=size,
        category=category,
        start_date=start_date,
        end_date=end_date,
        group_id=group_id,
        transaction_type=transaction_type
    )
    
    transaction_items = [
        Transaction(
            id=t.id,
            name=t.name,
            type=TransactionType(t.type.value),
            category=t.category,
            amount=t.amount,
            date=t.date,
            user_id=t.user_id,
            group_id=t.group_id,
            created_at=t.created_at,
            updated_at=t.updated_at
        )
        for t in transactions
    ]
    
    return TransactionListResponse(
        items=transaction_items,
        total=total,
        page=page,
        size=size
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
    repo = TransactionRepository(db)
    
    try:
        transaction = repo.create(
            name=request.name,
            type=request.type,
            category=request.category,
            amount=request.amount,
            transaction_date=request.date,
            user_id=current_user.id,
            group_id=request.group_id
        )
        
        return Transaction(
            id=transaction.id,
            name=transaction.name,
            type=TransactionType(transaction.type.value),
            category=transaction.category,
            amount=transaction.amount,
            date=transaction.date,
            user_id=transaction.user_id,
            group_id=transaction.group_id,
            created_at=transaction.created_at,
            updated_at=transaction.updated_at
        )
        
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
    repo = TransactionRepository(db)
    
    transaction = repo.get_by_id(transaction_id, user_id=current_user.id)
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Транзакция с ID {transaction_id} не найдена",
        )
    
    return Transaction(
        id=transaction.id,
        name=transaction.name,
        type=TransactionType(transaction.type.value),
        category=transaction.category,
        amount=transaction.amount,
        date=transaction.date,
        user_id=transaction.user_id,
        group_id=transaction.group_id,
        created_at=transaction.created_at,
        updated_at=transaction.updated_at
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
    repo = TransactionRepository(db)
    
    # Подготавливаем данные для обновления
    update_data = {}
    
    if request.name is not None:
        update_data['name'] = request.name
    
    if request.amount is not None:
        update_data['amount'] = request.amount
    
    if request.category is not None:
        update_data['category'] = request.category
    
    if request.date is not None:
        update_data['date'] = request.date
    
    if request.type is not None:
        update_data['type'] = request.type
    
    if request.group_id is not None:
        update_data['group_id'] = request.group_id
    
    try:
        transaction = repo.update(
            transaction_id=transaction_id,
            user_id=current_user.id,
            **update_data
        )
        
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Транзакция с ID {transaction_id} не найдена"
            )
        
        return Transaction(
            id=transaction.id,
            name=transaction.name,
            type=TransactionType(transaction.type.value),
            category=transaction.category,
            amount=transaction.amount,
            date=transaction.date,
            user_id=transaction.user_id,
            group_id=transaction.group_id,
            created_at=transaction.created_at,
            updated_at=transaction.updated_at
        )
        
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
    repo = TransactionRepository(db)
    
    try:
        deleted = repo.delete(transaction_id, user_id=current_user.id)
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

