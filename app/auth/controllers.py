"""Контроллеры для Auth API.

Автоматически сгенерировано из openapi-specs/auth-service.yaml
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.auth.models import (
    ChangePasswordRequest,
    ChangePasswordResponse,
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    User,
)
from app.core.dependencies import get_current_user
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.db.models import User as DBUser
from app.db.session import get_db
from app.repositories.user_repository import UserRepository

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=User,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация нового пользователя",
    description="Создание нового пользователя в системе",
    operation_id="register_user",
)
async def register_user(
    request: RegisterRequest,
    db: Session = Depends(get_db)
) -> User:
    """Регистрация нового пользователя.

    Args:
        request: Данные для регистрации
        db: Сессия базы данных

    Returns:
        User: Созданный пользователь

    Raises:
        HTTPException: Если пользователь с таким логином уже существует
    """
    repo = UserRepository(db)
    
    try:
        user = repo.add(
            first_name=request.first_name,
            last_name=request.last_name,
            login=request.login,
            password=request.password
        )
        
        return User(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            login=user.login,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка базы данных при регистрации пользователя"
        )


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Авторизация пользователя",
    description="Аутентификация пользователя и получение JWT токенов",
    operation_id="login_user",
)
async def login_user(
    request: LoginRequest,
    db: Session = Depends(get_db)
) -> LoginResponse:
    """Авторизация пользователя.

    Args:
        request: Данные для авторизации
        db: Сессия базы данных

    Returns:
        LoginResponse: Токены доступа и информация о пользователе

    Raises:
        HTTPException: Если неверный логин или пароль
    """
    repo = UserRepository(db)
    
    user = repo.verify_user(request.login, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль"
        )
    
    # Создаем токены (sub должен быть строкой по стандарту JWT)
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=User(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            login=user.login,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
    )


@router.post(
    "/token",
    response_model=TokenResponse,
    summary="OAuth2 авторизация",
    description="Авторизация через OAuth2 password flow (для Swagger UI)",
    operation_id="oauth2_login",
)
async def oauth2_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> TokenResponse:
    """OAuth2 авторизация (для Swagger Authorize).

    Args:
        form_data: username и password в form-data формате
        db: Сессия базы данных

    Returns:
        TokenResponse: Токены доступа
    """
    repo = UserRepository(db)
    
    # OAuth2 использует поле username, у нас это login
    user = repo.verify_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Обновление токена доступа",
    description="Обновление access токена с использованием refresh токена",
    operation_id="refresh_token",
)
async def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
) -> TokenResponse:
    """Обновление токена доступа.

    Args:
        request: Refresh токен
        db: Сессия базы данных

    Returns:
        TokenResponse: Новые токены доступа

    Raises:
        HTTPException: Если refresh токен неверный или истек
    """
    payload = decode_token(request.refresh_token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный или истекший refresh токен"
        )
    
    token_type = payload.get("type")
    if token_type != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный тип токена"
        )
    
    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный формат токена"
        )
    
    # Проверяем существование пользователя
    repo = UserRepository(db)
    user = repo.get_by_id(int(user_id_str))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден"
        )
    
    # Создаем новые токены (sub должен быть строкой по стандарту JWT)
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


@router.post(
    "/change-password",
    response_model=ChangePasswordResponse,
    summary="Смена пароля",
    description="Изменение пароля текущего авторизованного пользователя",
    operation_id="change_password",
)
async def change_password(
    request: ChangePasswordRequest,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ChangePasswordResponse:
    """Смена пароля.

    Args:
        request: Текущий и новый пароль
        current_user: Текущий авторизованный пользователь
        db: Сессия базы данных

    Returns:
        ChangePasswordResponse: Подтверждение смены пароля

    Raises:
        HTTPException: Если текущий пароль неверный или не авторизован
    """
    repo = UserRepository(db)
    
    # Проверяем текущий пароль
    user = repo.verify_user(current_user.login, request.current_password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный текущий пароль"
        )
    
    # Обновляем пароль
    try:
        repo.update_password(current_user.id, request.new_password)
        return ChangePasswordResponse(message="Пароль успешно изменен")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка базы данных при смене пароля"
        )


@router.get(
    "/me",
    response_model=User,
    summary="Получить информацию о текущем пользователе",
    description="Получение информации о текущем авторизованном пользователе",
    operation_id="get_current_user",
)
async def get_current_user_info(
    current_user: DBUser = Depends(get_current_user)
) -> User:
    """Получить информацию о текущем пользователе.

    Args:
        current_user: Текущий авторизованный пользователь

    Returns:
        User: Информация о пользователе

    Raises:
        HTTPException: Если не авторизован
    """
    return User(
        id=current_user.id,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        login=current_user.login,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )

