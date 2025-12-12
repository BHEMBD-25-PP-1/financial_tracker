"""Контроллеры для Groups API.

Автоматически сгенерировано из openapi-specs/groups-service.yaml
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.models import User as DBUser, GroupRole as DBGroupRole
from app.db.session import get_db
from app.groups.models import (
    AddMemberRequest,
    CategoryStatistic,
    CreateGroupRequest,
    Group,
    GroupAnalyticsResponse,
    GroupListResponse,
    GroupMember,
    GroupMembersResponse,
    GroupRole,
    PeriodInfo,
    UpdateGroupRequest,
    UserInfo,
)
from app.repositories.group_repository import GroupRepository
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.user_repository import UserRepository

router = APIRouter(prefix="/groups", tags=["groups"])


@router.get(
    "",
    response_model=GroupListResponse,
    summary="Получить список групп пользователя",
    description="Получить все группы, в которых участвует текущий пользователь",
    operation_id="get_groups",
)
async def get_groups(
    page: int = Query(default=1, description="Номер страницы", ge=1),
    size: int = Query(default=20, description="Размер страницы", ge=1, le=100),
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> GroupListResponse:
    """Получить список групп пользователя.

    Args:
        page: Номер страницы
        size: Размер страницы
        current_user: Текущий авторизованный пользователь
        db: Сессия базы данных

    Returns:
        GroupListResponse: Список групп с метаданными пагинации
    """
    repo = GroupRepository(db)
    
    skip = (page - 1) * size
    groups, total = repo.get_by_user_id(current_user.id, skip=skip, limit=size)
    
    group_items = [
        Group(
            id=g.id,
            name=g.name,
            owner_id=g.owner_id,
            created_at=g.created_at,
            updated_at=g.updated_at
        )
        for g in groups
    ]
    
    return GroupListResponse(
        items=group_items,
        total=total,
        page=page,
        size=size
    )


@router.post(
    "",
    response_model=Group,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новую группу",
    description="Создание новой группы пользователей",
    operation_id="create_group",
)
async def create_group(
    request: CreateGroupRequest,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Group:
    """Создать новую группу.

    Args:
        request: Данные для создания группы
        current_user: Текущий авторизованный пользователь
        db: Сессия базы данных

    Returns:
        Group: Созданная группа
    """
    repo = GroupRepository(db)
    
    try:
        group = repo.create(name=request.name, owner_id=current_user.id)
        return Group(
            id=group.id,
            name=group.name,
            owner_id=group.owner_id,
            created_at=group.created_at,
            updated_at=group.updated_at
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка базы данных при создании группы"
        )


@router.get(
    "/{group_id}",
    response_model=Group,
    summary="Получить группу по ID",
    description="Получение информации о группе по её идентификатору",
    operation_id="get_group_by_id",
)
async def get_group_by_id(
    group_id: int,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Group:
    """Получить группу по ID.

    Args:
        group_id: ID группы
        current_user: Текущий авторизованный пользователь
        db: Сессия базы данных

    Returns:
        Group: Группа

    Raises:
        HTTPException: Если группа не найдена или нет доступа
    """
    repo = GroupRepository(db)
    
    group = repo.get_by_id(group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Группа с ID {group_id} не найдена",
        )
    
    if not repo.is_member(group_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к этой группе",
        )
    
    return Group(
        id=group.id,
        name=group.name,
        owner_id=group.owner_id,
        created_at=group.created_at,
        updated_at=group.updated_at
    )


@router.put(
    "/{group_id}",
    response_model=Group,
    summary="Обновить группу",
    description="Обновление информации о группе (только для владельца)",
    operation_id="update_group",
)
async def update_group(
    group_id: int,
    request: UpdateGroupRequest,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Group:
    """Обновить группу.

    Args:
        group_id: ID группы
        request: Данные для обновления группы
        current_user: Текущий авторизованный пользователь
        db: Сессия базы данных

    Returns:
        Group: Обновленная группа

    Raises:
        HTTPException: Если группа не найдена или нет прав
    """
    repo = GroupRepository(db)
    
    try:
        group = repo.update(group_id, current_user.id, name=request.name)
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Группа с ID {group_id} не найдена или нет прав на обновление",
            )
        
        return Group(
            id=group.id,
            name=group.name,
            owner_id=group.owner_id,
            created_at=group.created_at,
            updated_at=group.updated_at
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка базы данных при обновлении группы"
        )


@router.delete(
    "/{group_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить группу",
    description="Удаление группы (только для владельца)",
    operation_id="delete_group",
)
async def delete_group(
    group_id: int,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Response:
    """Удалить группу.

    Args:
        group_id: ID группы
        current_user: Текущий авторизованный пользователь
        db: Сессия базы данных

    Returns:
        Response: Пустой ответ со статусом 204

    Raises:
        HTTPException: Если группа не найдена или нет прав
    """
    repo = GroupRepository(db)
    
    try:
        deleted = repo.delete(group_id, current_user.id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Группа с ID {group_id} не найдена или нет прав на удаление",
            )
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка базы данных при удалении группы"
        )


@router.get(
    "/{group_id}/members",
    response_model=GroupMembersResponse,
    summary="Получить список участников группы",
    description="Получение списка всех участников группы",
    operation_id="get_group_members",
)
async def get_group_members(
    group_id: int,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> GroupMembersResponse:
    """Получить список участников группы.

    Args:
        group_id: ID группы
        current_user: Текущий авторизованный пользователь
        db: Сессия базы данных

    Returns:
        GroupMembersResponse: Список участников группы

    Raises:
        HTTPException: Если группа не найдена или нет доступа
    """
    repo = GroupRepository(db)
    
    if not repo.is_member(group_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к этой группе",
        )
    
    members = repo.get_members(group_id)
    
    member_items = []
    for m in members:
        user_info = None
        if m.user:
            user_info = UserInfo(
                id=m.user.id,
                first_name=m.user.first_name,
                last_name=m.user.last_name,
                login=m.user.login
            )
        
        member_items.append(
            GroupMember(
                id=m.id,
                user_id=m.user_id,
                group_id=m.group_id,
                role=GroupRole(m.role.value.upper()),
                joined_at=m.joined_at,
                user=user_info
            )
        )
    
    return GroupMembersResponse(members=member_items)


@router.post(
    "/{group_id}/members",
    response_model=GroupMember,
    status_code=status.HTTP_201_CREATED,
    summary="Добавить участника в группу",
    description="Добавление нового участника в группу (только для владельца)",
    operation_id="add_group_member",
)
async def add_group_member(
    group_id: int,
    request: AddMemberRequest,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> GroupMember:
    """Добавить участника в группу.

    Args:
        group_id: ID группы
        request: Данные для добавления участника
        current_user: Текущий авторизованный пользователь
        db: Сессия базы данных

    Returns:
        GroupMember: Добавленный участник

    Raises:
        HTTPException: Если группа или пользователь не найдены, или нет прав
    """
    repo = GroupRepository(db)
    
    try:
        user_group = repo.add_member(
            group_id=group_id,
            user_id=request.user_id,
            owner_id=current_user.id,
            role=DBGroupRole.MEMBER
        )
        
        user_repo = UserRepository(db)
        user = user_repo.get_by_id(request.user_id)
        user_info = None
        if user:
            user_info = UserInfo(
                id=user.id,
                first_name=user.first_name,
                last_name=user.last_name,
                login=user.login
            )
        
        return GroupMember(
            id=user_group.id,
            user_id=user_group.user_id,
            group_id=user_group.group_id,
            role=GroupRole(user_group.role.value.upper()),
            joined_at=user_group.joined_at,
            user=user_info
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка базы данных при добавлении участника"
        )


@router.delete(
    "/{group_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить участника из группы",
    description="Удаление участника из группы (только для владельца или самого участника)",
    operation_id="remove_group_member",
)
async def remove_group_member(
    group_id: int,
    user_id: int,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Response:
    """Удалить участника из группы.

    Args:
        group_id: ID группы
        user_id: ID пользователя
        current_user: Текущий авторизованный пользователь
        db: Сессия базы данных

    Returns:
        Response: Пустой ответ со статусом 204

    Raises:
        HTTPException: Если группа или участник не найдены, или нет прав
    """
    repo = GroupRepository(db)
    
    try:
        removed = repo.remove_member(group_id, user_id, current_user.id)
        if not removed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Участник не найден или нет прав на удаление",
            )
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка базы данных при удалении участника"
        )


@router.get(
    "/{group_id}/analytics",
    response_model=GroupAnalyticsResponse,
    summary="Получить аналитику по группе",
    description="Получение аналитики по транзакциям группы",
    operation_id="get_group_analytics",
)
async def get_group_analytics(
    group_id: int,
    start_date: Optional[date] = Query(
        default=None, description="Дата начала периода (YYYY-MM-DD)"
    ),
    end_date: Optional[date] = Query(
        default=None, description="Дата окончания периода (YYYY-MM-DD)"
    ),
    group_by: str = Query(
        default="category", description="Группировка данных", enum=["category", "user", "date"]
    ),
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> GroupAnalyticsResponse:
    """Получить аналитику по группе.

    Args:
        group_id: ID группы
        start_date: Дата начала периода
        end_date: Дата окончания периода
        group_by: Тип группировки данных
        current_user: Текущий авторизованный пользователь
        db: Сессия базы данных

    Returns:
        GroupAnalyticsResponse: Аналитика по группе

    Raises:
        HTTPException: Если группа не найдена или нет доступа
    """
    repo = GroupRepository(db)
    
    if not repo.is_member(group_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к этой группе",
        )
    
    trans_repo = TransactionRepository(db)
    transactions, _ = trans_repo.get_all(
        user_id=None,
        skip=0,
        limit=10000,
        start_date=start_date,
        end_date=end_date,
        group_id=group_id
    )
    
    total_income = sum(t.amount for t in transactions if t.type.value.upper() == "INCOME")
    total_expense = sum(t.amount for t in transactions if t.type.value.upper() == "EXPENSE")
    balance = total_income - total_expense
    
    category_stats = {}
    for t in transactions:
        if t.category not in category_stats:
            category_stats[t.category] = {"total": 0.0, "count": 0}
        category_stats[t.category]["total"] += t.amount
        category_stats[t.category]["count"] += 1
    
    statistics = [
        CategoryStatistic(
            category=cat,
            total_amount=stats["total"],
            transaction_count=stats["count"]
        )
        for cat, stats in category_stats.items()
    ]
    
    period = None
    if start_date or end_date:
        period = PeriodInfo(start_date=start_date, end_date=end_date)
    
    return GroupAnalyticsResponse(
        group_id=group_id,
        total_income=total_income,
        total_expense=total_expense,
        balance=balance,
        statistics=statistics,
        period=period
    )

