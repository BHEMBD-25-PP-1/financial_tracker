"""Тесты для Pydantic моделей аутентификации."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from app.auth.models import (
    RegisterRequest,
    LoginRequest,
    RefreshTokenRequest,
    ChangePasswordRequest,
    ChangePasswordResponse,
    User,
    LoginResponse,
    TokenResponse,
    Error,
)


class TestRegisterRequest:
    """Тесты для модели RegisterRequest."""

    def test_valid_register_request(self):
        """Тест создания валидного запроса на регистрацию."""
        request = RegisterRequest(
            first_name="Иван",
            last_name="Иванов",
            login="ivan_user",
            password="securePassword123"
        )
        
        assert request.first_name == "Иван"
        assert request.last_name == "Иванов"
        assert request.login == "ivan_user"
        assert request.password == "securePassword123"

    def test_login_min_length(self):
        """Тест минимальной длины логина (3 символа)."""
        # Должен пройти
        request = RegisterRequest(
            first_name="Иван",
            last_name="Иванов",
            login="abc",
            password="securePassword123"
        )
        assert request.login == "abc"
        
        # Должен упасть
        with pytest.raises(ValidationError):
            RegisterRequest(
                first_name="Иван",
                last_name="Иванов",
                login="ab",  # Слишком короткий
                password="securePassword123"
            )

    def test_login_max_length(self):
        """Тест максимальной длины логина (50 символов)."""
        # Должен пройти
        request = RegisterRequest(
            first_name="Иван",
            last_name="Иванов",
            login="a" * 50,
            password="securePassword123"
        )
        assert len(request.login) == 50
        
        # Должен упасть
        with pytest.raises(ValidationError):
            RegisterRequest(
                first_name="Иван",
                last_name="Иванов",
                login="a" * 51,  # Слишком длинный
                password="securePassword123"
            )

    def test_login_pattern_valid(self):
        """Тест валидных паттернов логина."""
        valid_logins = ["user123", "User_Name", "test_user_1", "ABC", "user_"]
        
        for login in valid_logins:
            request = RegisterRequest(
                first_name="Иван",
                last_name="Иванов",
                login=login,
                password="securePassword123"
            )
            assert request.login == login

    def test_login_pattern_invalid(self):
        """Тест невалидных паттернов логина."""
        invalid_logins = ["user@name", "user-name", "user.name", "user name", "пользователь"]
        
        for login in invalid_logins:
            with pytest.raises(ValidationError):
                RegisterRequest(
                    first_name="Иван",
                    last_name="Иванов",
                    login=login,
                    password="securePassword123"
                )

    def test_password_min_length(self):
        """Тест минимальной длины пароля (8 символов)."""
        # Должен пройти
        request = RegisterRequest(
            first_name="Иван",
            last_name="Иванов",
            login="ivan_user",
            password="12345678"
        )
        assert len(request.password) == 8
        
        # Должен упасть
        with pytest.raises(ValidationError):
            RegisterRequest(
                first_name="Иван",
                last_name="Иванов",
                login="ivan_user",
                password="1234567"  # Слишком короткий
            )

    def test_password_max_length(self):
        """Тест максимальной длины пароля (100 символов)."""
        # Должен пройти
        request = RegisterRequest(
            first_name="Иван",
            last_name="Иванов",
            login="ivan_user",
            password="a" * 100
        )
        assert len(request.password) == 100
        
        # Должен упасть
        with pytest.raises(ValidationError):
            RegisterRequest(
                first_name="Иван",
                last_name="Иванов",
                login="ivan_user",
                password="a" * 101  # Слишком длинный
            )

    def test_first_name_min_length(self):
        """Тест минимальной длины имени (1 символ)."""
        request = RegisterRequest(
            first_name="И",
            last_name="Иванов",
            login="ivan_user",
            password="securePassword123"
        )
        assert request.first_name == "И"

    def test_first_name_max_length(self):
        """Тест максимальной длины имени (100 символов)."""
        # Должен пройти
        request = RegisterRequest(
            first_name="И" * 100,
            last_name="Иванов",
            login="ivan_user",
            password="securePassword123"
        )
        assert len(request.first_name) == 100
        
        # Должен упасть
        with pytest.raises(ValidationError):
            RegisterRequest(
                first_name="И" * 101,
                last_name="Иванов",
                login="ivan_user",
                password="securePassword123"
            )

    def test_empty_first_name(self):
        """Тест пустого имени."""
        with pytest.raises(ValidationError):
            RegisterRequest(
                first_name="",
                last_name="Иванов",
                login="ivan_user",
                password="securePassword123"
            )

    def test_last_name_constraints(self):
        """Тест ограничений фамилии."""
        # Пустая фамилия
        with pytest.raises(ValidationError):
            RegisterRequest(
                first_name="Иван",
                last_name="",
                login="ivan_user",
                password="securePassword123"
            )
        
        # Слишком длинная фамилия
        with pytest.raises(ValidationError):
            RegisterRequest(
                first_name="Иван",
                last_name="И" * 101,
                login="ivan_user",
                password="securePassword123"
            )

    def test_missing_required_fields(self):
        """Тест отсутствия обязательных полей."""
        with pytest.raises(ValidationError):
            RegisterRequest(
                first_name="Иван",
                last_name="Иванов"
                # login и password отсутствуют
            )


class TestLoginRequest:
    """Тесты для модели LoginRequest."""

    def test_valid_login_request(self):
        """Тест создания валидного запроса на авторизацию."""
        request = LoginRequest(
            login="ivan_user",
            password="securePassword123"
        )
        
        assert request.login == "ivan_user"
        assert request.password == "securePassword123"

    def test_empty_login(self):
        """Тест пустого логина."""
        with pytest.raises(ValidationError):
            LoginRequest(
                login="",
                password="securePassword123"
            )

    def test_empty_password(self):
        """Тест пустого пароля."""
        with pytest.raises(ValidationError):
            LoginRequest(
                login="ivan_user",
                password=""
            )

    def test_missing_login(self):
        """Тест отсутствия логина."""
        with pytest.raises(ValidationError):
            LoginRequest(
                password="securePassword123"
            )

    def test_missing_password(self):
        """Тест отсутствия пароля."""
        with pytest.raises(ValidationError):
            LoginRequest(
                login="ivan_user"
            )


class TestRefreshTokenRequest:
    """Тесты для модели RefreshTokenRequest."""

    def test_valid_refresh_token_request(self):
        """Тест создания валидного запроса на обновление токена."""
        request = RefreshTokenRequest(
            refresh_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        )
        
        assert request.refresh_token == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

    def test_empty_refresh_token(self):
        """Тест пустого refresh токена."""
        with pytest.raises(ValidationError):
            RefreshTokenRequest(
                refresh_token=""
            )

    def test_missing_refresh_token(self):
        """Тест отсутствия refresh токена."""
        with pytest.raises(ValidationError):
            RefreshTokenRequest()


class TestChangePasswordRequest:
    """Тесты для модели ChangePasswordRequest."""

    def test_valid_change_password_request(self):
        """Тест создания валидного запроса на смену пароля."""
        request = ChangePasswordRequest(
            current_password="oldPassword123",
            new_password="newSecurePassword456"
        )
        
        assert request.current_password == "oldPassword123"
        assert request.new_password == "newSecurePassword456"

    def test_new_password_min_length(self):
        """Тест минимальной длины нового пароля (8 символов)."""
        # Должен пройти
        request = ChangePasswordRequest(
            current_password="oldPassword123",
            new_password="12345678"
        )
        assert len(request.new_password) == 8
        
        # Должен упасть
        with pytest.raises(ValidationError):
            ChangePasswordRequest(
                current_password="oldPassword123",
                new_password="1234567"  # Слишком короткий
            )

    def test_new_password_max_length(self):
        """Тест максимальной длины нового пароля (100 символов)."""
        # Должен пройти
        request = ChangePasswordRequest(
            current_password="oldPassword123",
            new_password="a" * 100
        )
        assert len(request.new_password) == 100
        
        # Должен упасть
        with pytest.raises(ValidationError):
            ChangePasswordRequest(
                current_password="oldPassword123",
                new_password="a" * 101  # Слишком длинный
            )

    def test_empty_current_password(self):
        """Тест пустого текущего пароля."""
        with pytest.raises(ValidationError):
            ChangePasswordRequest(
                current_password="",
                new_password="newSecurePassword456"
            )

    def test_missing_fields(self):
        """Тест отсутствия обязательных полей."""
        with pytest.raises(ValidationError):
            ChangePasswordRequest(
                current_password="oldPassword123"
                # new_password отсутствует
            )


class TestChangePasswordResponse:
    """Тесты для модели ChangePasswordResponse."""

    def test_default_message(self):
        """Тест значения по умолчанию."""
        response = ChangePasswordResponse()
        
        assert response.message == "Пароль успешно изменен"

    def test_custom_message(self):
        """Тест пользовательского сообщения."""
        response = ChangePasswordResponse(message="Пароль обновлен")
        
        assert response.message == "Пароль обновлен"


class TestUser:
    """Тесты для модели User."""

    def test_valid_user(self):
        """Тест создания валидного пользователя."""
        now = datetime.now()
        user = User(
            id=1,
            first_name="Иван",
            last_name="Иванов",
            login="ivan_user",
            created_at=now,
            updated_at=now
        )
        
        assert user.id == 1
        assert user.first_name == "Иван"
        assert user.last_name == "Иванов"
        assert user.login == "ivan_user"
        assert user.created_at == now
        assert user.updated_at == now

    def test_missing_required_fields(self):
        """Тест отсутствия обязательных полей."""
        with pytest.raises(ValidationError):
            User(
                id=1,
                first_name="Иван",
                last_name="Иванов"
                # login, created_at, updated_at отсутствуют
            )


class TestLoginResponse:
    """Тесты для модели LoginResponse."""

    def test_valid_login_response(self):
        """Тест создания валидного ответа на авторизацию."""
        now = datetime.now()
        user = User(
            id=1,
            first_name="Иван",
            last_name="Иванов",
            login="ivan_user",
            created_at=now,
            updated_at=now
        )
        
        response = LoginResponse(
            access_token="access_token_123",
            refresh_token="refresh_token_456",
            token_type="bearer",
            user=user
        )
        
        assert response.access_token == "access_token_123"
        assert response.refresh_token == "refresh_token_456"
        assert response.token_type == "bearer"
        assert response.user.id == 1

    def test_default_token_type(self):
        """Тест значения token_type по умолчанию."""
        now = datetime.now()
        user = User(
            id=1,
            first_name="Иван",
            last_name="Иванов",
            login="ivan_user",
            created_at=now,
            updated_at=now
        )
        
        response = LoginResponse(
            access_token="access_token_123",
            refresh_token="refresh_token_456",
            user=user
        )
        
        assert response.token_type == "bearer"


class TestTokenResponse:
    """Тесты для модели TokenResponse."""

    def test_valid_token_response(self):
        """Тест создания валидного ответа с токенами."""
        response = TokenResponse(
            access_token="access_token_123",
            refresh_token="refresh_token_456",
            token_type="bearer"
        )
        
        assert response.access_token == "access_token_123"
        assert response.refresh_token == "refresh_token_456"
        assert response.token_type == "bearer"

    def test_default_token_type(self):
        """Тест значения token_type по умолчанию."""
        response = TokenResponse(
            access_token="access_token_123",
            refresh_token="refresh_token_456"
        )
        
        assert response.token_type == "bearer"

    def test_missing_tokens(self):
        """Тест отсутствия токенов."""
        with pytest.raises(ValidationError):
            TokenResponse(
                access_token="access_token_123"
                # refresh_token отсутствует
            )


class TestError:
    """Тесты для модели Error."""

    def test_valid_error(self):
        """Тест создания валидной ошибки."""
        error = Error(
            detail="Описание ошибки",
            error_code="VALIDATION_ERROR"
        )
        
        assert error.detail == "Описание ошибки"
        assert error.error_code == "VALIDATION_ERROR"

    def test_error_without_code(self):
        """Тест ошибки без error_code."""
        error = Error(
            detail="Описание ошибки"
        )
        
        assert error.detail == "Описание ошибки"
        assert error.error_code is None

    def test_missing_detail(self):
        """Тест отсутствия detail."""
        with pytest.raises(ValidationError):
            Error(
                error_code="VALIDATION_ERROR"
                # detail отсутствует
            )

