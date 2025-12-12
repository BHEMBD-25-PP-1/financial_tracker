"""Тесты для контроллеров аутентификации."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime

from main import app
from app.core.dependencies import get_current_user, get_db
from app.db.models import User as DBUser


# Фикстура для мок пользователя БД
@pytest.fixture
def mock_db_user():
    """Мок пользователя из базы данных."""
    user = MagicMock(unsafe_spec=DBUser)
    user.id = 1
    user.first_name = "Иван"
    user.last_name = "Иванов"
    user.login = "ivan_user"
    user.created_at = datetime(2024, 1, 15, 10, 0, 0)
    user.updated_at = datetime(2024, 1, 15, 10, 0, 0)
    return user


@pytest.fixture
def client_with_auth(mock_db_user):
    """TestClient с переопределёнными зависимостями для авторизации."""
    app.dependency_overrides[get_current_user] = lambda: mock_db_user
    app.dependency_overrides[get_db] = lambda: MagicMock()
    client = TestClient(app)
    yield client
    # Очищаем переопределения после теста
    app.dependency_overrides.clear()


@pytest.fixture
def client_no_auth():
    """TestClient без переопределённой авторизации."""
    app.dependency_overrides[get_db] = lambda: MagicMock()
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


class TestRegisterUser:
    """Тесты для эндпоинта регистрации."""

    @patch("app.auth.controllers.UserRepository")
    def test_register_success(self, mock_repo_class, client_no_auth, mock_db_user):
        """Тест успешной регистрации пользователя."""
        mock_repo = MagicMock()
        mock_repo.add.return_value = mock_db_user
        mock_repo_class.return_value = mock_repo

        response = client_no_auth.post(
            "/api/v1/auth/register",
            json={
                "first_name": "Иван",
                "last_name": "Иванов",
                "login": "ivan_user",
                "password": "securePassword123"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == 1
        assert data["first_name"] == "Иван"
        assert data["last_name"] == "Иванов"
        assert data["login"] == "ivan_user"

    @patch("app.auth.controllers.UserRepository")
    def test_register_duplicate_login(self, mock_repo_class, client_no_auth):
        """Тест регистрации с уже существующим логином."""
        mock_repo = MagicMock()
        mock_repo.add.side_effect = ValueError("Пользователь с таким логином уже существует")
        mock_repo_class.return_value = mock_repo

        response = client_no_auth.post(
            "/api/v1/auth/register",
            json={
                "first_name": "Иван",
                "last_name": "Иванов",
                "login": "existing_user",
                "password": "securePassword123"
            }
        )

        assert response.status_code == 400
        assert "уже существует" in response.json()["detail"]

    @patch("app.auth.controllers.UserRepository")
    def test_register_database_error(self, mock_repo_class, client_no_auth):
        """Тест обработки ошибки базы данных при регистрации."""
        mock_repo = MagicMock()
        mock_repo.add.side_effect = RuntimeError("Database connection error")
        mock_repo_class.return_value = mock_repo

        response = client_no_auth.post(
            "/api/v1/auth/register",
            json={
                "first_name": "Иван",
                "last_name": "Иванов",
                "login": "ivan_user",
                "password": "securePassword123"
            }
        )

        assert response.status_code == 500
        assert "Ошибка базы данных" in response.json()["detail"]

    def test_register_invalid_login_format(self, client_no_auth):
        """Тест регистрации с невалидным форматом логина."""
        response = client_no_auth.post(
            "/api/v1/auth/register",
            json={
                "first_name": "Иван",
                "last_name": "Иванов",
                "login": "ivan@user",  # Недопустимый символ
                "password": "securePassword123"
            }
        )

        assert response.status_code == 422  # Validation error

    def test_register_short_password(self, client_no_auth):
        """Тест регистрации с коротким паролем."""
        response = client_no_auth.post(
            "/api/v1/auth/register",
            json={
                "first_name": "Иван",
                "last_name": "Иванов",
                "login": "ivan_user",
                "password": "short"  # Меньше 8 символов
            }
        )

        assert response.status_code == 422

    def test_register_short_login(self, client_no_auth):
        """Тест регистрации с коротким логином."""
        response = client_no_auth.post(
            "/api/v1/auth/register",
            json={
                "first_name": "Иван",
                "last_name": "Иванов",
                "login": "ab",  # Меньше 3 символов
                "password": "securePassword123"
            }
        )

        assert response.status_code == 422

    def test_register_missing_fields(self, client_no_auth):
        """Тест регистрации без обязательных полей."""
        response = client_no_auth.post(
            "/api/v1/auth/register",
            json={
                "first_name": "Иван"
                # Остальные поля отсутствуют
            }
        )

        assert response.status_code == 422


class TestLoginUser:
    """Тесты для эндпоинта авторизации."""

    @patch("app.auth.controllers.create_refresh_token")
    @patch("app.auth.controllers.create_access_token")
    @patch("app.auth.controllers.UserRepository")
    def test_login_success(self, mock_repo_class, mock_create_access, mock_create_refresh, 
                          client_no_auth, mock_db_user):
        """Тест успешной авторизации."""
        mock_repo = MagicMock()
        mock_repo.verify_user.return_value = mock_db_user
        mock_repo_class.return_value = mock_repo
        mock_create_access.return_value = "access_token_123"
        mock_create_refresh.return_value = "refresh_token_456"

        response = client_no_auth.post(
            "/api/v1/auth/login",
            json={
                "login": "ivan_user",
                "password": "securePassword123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "access_token_123"
        assert data["refresh_token"] == "refresh_token_456"
        assert data["token_type"] == "bearer"
        assert data["user"]["id"] == 1
        assert data["user"]["login"] == "ivan_user"

    @patch("app.auth.controllers.UserRepository")
    def test_login_invalid_credentials(self, mock_repo_class, client_no_auth):
        """Тест авторизации с неверными учетными данными."""
        mock_repo = MagicMock()
        mock_repo.verify_user.return_value = None
        mock_repo_class.return_value = mock_repo

        response = client_no_auth.post(
            "/api/v1/auth/login",
            json={
                "login": "ivan_user",
                "password": "wrongPassword"
            }
        )

        assert response.status_code == 401
        assert "Неверный логин или пароль" in response.json()["detail"]

    @patch("app.auth.controllers.UserRepository")
    def test_login_nonexistent_user(self, mock_repo_class, client_no_auth):
        """Тест авторизации несуществующего пользователя."""
        mock_repo = MagicMock()
        mock_repo.verify_user.return_value = None
        mock_repo_class.return_value = mock_repo

        response = client_no_auth.post(
            "/api/v1/auth/login",
            json={
                "login": "nonexistent_user",
                "password": "somePassword123"
            }
        )

        assert response.status_code == 401
        assert "Неверный логин или пароль" in response.json()["detail"]

    def test_login_missing_fields(self, client_no_auth):
        """Тест авторизации без обязательных полей."""
        response = client_no_auth.post(
            "/api/v1/auth/login",
            json={
                "login": "ivan_user"
                # password отсутствует
            }
        )

        assert response.status_code == 422


class TestOAuth2Login:
    """Тесты для OAuth2 авторизации."""

    @patch("app.auth.controllers.create_refresh_token")
    @patch("app.auth.controllers.create_access_token")
    @patch("app.auth.controllers.UserRepository")
    def test_oauth2_login_success(self, mock_repo_class, mock_create_access, 
                                   mock_create_refresh, client_no_auth, mock_db_user):
        """Тест успешной OAuth2 авторизации."""
        mock_repo = MagicMock()
        mock_repo.verify_user.return_value = mock_db_user
        mock_repo_class.return_value = mock_repo
        mock_create_access.return_value = "access_token_123"
        mock_create_refresh.return_value = "refresh_token_456"

        response = client_no_auth.post(
            "/api/v1/auth/token",
            data={
                "username": "ivan_user",
                "password": "securePassword123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "access_token_123"
        assert data["refresh_token"] == "refresh_token_456"
        assert data["token_type"] == "bearer"

    @patch("app.auth.controllers.UserRepository")
    def test_oauth2_login_invalid_credentials(self, mock_repo_class, client_no_auth):
        """Тест OAuth2 авторизации с неверными учетными данными."""
        mock_repo = MagicMock()
        mock_repo.verify_user.return_value = None
        mock_repo_class.return_value = mock_repo

        response = client_no_auth.post(
            "/api/v1/auth/token",
            data={
                "username": "ivan_user",
                "password": "wrongPassword"
            }
        )

        assert response.status_code == 401
        assert "Неверный логин или пароль" in response.json()["detail"]


class TestRefreshToken:
    """Тесты для обновления токена."""

    @patch("app.auth.controllers.create_refresh_token")
    @patch("app.auth.controllers.create_access_token")
    @patch("app.auth.controllers.UserRepository")
    @patch("app.auth.controllers.decode_token")
    def test_refresh_token_success(self, mock_decode, mock_repo_class, 
                                    mock_create_access, mock_create_refresh, 
                                    client_no_auth, mock_db_user):
        """Тест успешного обновления токена."""
        mock_decode.return_value = {"sub": "1", "type": "refresh"}
        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = mock_db_user
        mock_repo_class.return_value = mock_repo
        mock_create_access.return_value = "new_access_token"
        mock_create_refresh.return_value = "new_refresh_token"

        response = client_no_auth.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "valid_refresh_token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "new_access_token"
        assert data["refresh_token"] == "new_refresh_token"
        assert data["token_type"] == "bearer"

    @patch("app.auth.controllers.decode_token")
    def test_refresh_token_invalid(self, mock_decode, client_no_auth):
        """Тест обновления с невалидным refresh токеном."""
        mock_decode.return_value = None

        response = client_no_auth.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid_token"}
        )

        assert response.status_code == 401
        assert "Неверный или истекший refresh токен" in response.json()["detail"]

    @patch("app.auth.controllers.decode_token")
    def test_refresh_token_wrong_type(self, mock_decode, client_no_auth):
        """Тест обновления с токеном неверного типа (access вместо refresh)."""
        mock_decode.return_value = {"sub": "1", "type": "access"}

        response = client_no_auth.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "access_token_instead"}
        )

        assert response.status_code == 401
        assert "Неверный тип токена" in response.json()["detail"]

    @patch("app.auth.controllers.decode_token")
    def test_refresh_token_missing_sub(self, mock_decode, client_no_auth):
        """Тест обновления с токеном без sub."""
        mock_decode.return_value = {"type": "refresh"}  # sub отсутствует

        response = client_no_auth.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "token_without_sub"}
        )

        assert response.status_code == 401
        assert "Неверный формат токена" in response.json()["detail"]

    @patch("app.auth.controllers.UserRepository")
    @patch("app.auth.controllers.decode_token")
    def test_refresh_token_user_not_found(self, mock_decode, mock_repo_class, client_no_auth):
        """Тест обновления токена для несуществующего пользователя."""
        mock_decode.return_value = {"sub": "999", "type": "refresh"}
        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = None
        mock_repo_class.return_value = mock_repo

        response = client_no_auth.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "token_for_deleted_user"}
        )

        assert response.status_code == 401
        assert "Пользователь не найден" in response.json()["detail"]


class TestChangePassword:
    """Тесты для смены пароля."""

    @patch("app.auth.controllers.UserRepository")
    def test_change_password_success(self, mock_repo_class, client_with_auth, mock_db_user):
        """Тест успешной смены пароля."""
        mock_repo = MagicMock()
        mock_repo.verify_user.return_value = mock_db_user
        mock_repo.update_password.return_value = None
        mock_repo_class.return_value = mock_repo

        response = client_with_auth.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": "oldPassword123",
                "new_password": "newSecurePassword456"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Пароль успешно изменен"

    @patch("app.auth.controllers.UserRepository")
    def test_change_password_wrong_current(self, mock_repo_class, client_with_auth):
        """Тест смены пароля с неверным текущим паролем."""
        mock_repo = MagicMock()
        mock_repo.verify_user.return_value = None
        mock_repo_class.return_value = mock_repo

        response = client_with_auth.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": "wrongPassword",
                "new_password": "newSecurePassword456"
            }
        )

        assert response.status_code == 400
        assert "Неверный текущий пароль" in response.json()["detail"]

    @patch("app.auth.controllers.UserRepository")
    def test_change_password_validation_error(self, mock_repo_class, client_with_auth, mock_db_user):
        """Тест смены пароля с ошибкой валидации нового пароля."""
        mock_repo = MagicMock()
        mock_repo.verify_user.return_value = mock_db_user
        mock_repo.update_password.side_effect = ValueError("Пароль слишком слабый")
        mock_repo_class.return_value = mock_repo

        response = client_with_auth.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": "oldPassword123",
                "new_password": "weakpass"
            }
        )

        assert response.status_code == 400
        assert "Пароль слишком слабый" in response.json()["detail"]

    @patch("app.auth.controllers.UserRepository")
    def test_change_password_database_error(self, mock_repo_class, client_with_auth, mock_db_user):
        """Тест обработки ошибки базы данных при смене пароля."""
        mock_repo = MagicMock()
        mock_repo.verify_user.return_value = mock_db_user
        mock_repo.update_password.side_effect = RuntimeError("Database error")
        mock_repo_class.return_value = mock_repo

        response = client_with_auth.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": "oldPassword123",
                "new_password": "newSecurePassword456"
            }
        )

        assert response.status_code == 500
        assert "Ошибка базы данных" in response.json()["detail"]

    def test_change_password_short_new_password(self, client_with_auth):
        """Тест смены пароля с коротким новым паролем."""
        response = client_with_auth.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": "oldPassword123",
                "new_password": "short"  # Меньше 8 символов
            }
        )

        assert response.status_code == 422


class TestGetCurrentUserInfo:
    """Тесты для получения информации о текущем пользователе."""

    def test_get_current_user_info_success(self, client_with_auth):
        """Тест успешного получения информации о пользователе."""
        response = client_with_auth.get("/api/v1/auth/me")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["first_name"] == "Иван"
        assert data["last_name"] == "Иванов"
        assert data["login"] == "ivan_user"

    def test_get_current_user_info_unauthorized(self):
        """Тест получения информации без авторизации."""
        # Создаём клиент без переопределённых зависимостей
        app.dependency_overrides.clear()
        client = TestClient(app)
        
        response = client.get("/api/v1/auth/me")

        # Без токена должен быть 401 (Unauthorized) или 403 (Forbidden)
        assert response.status_code in [401, 403]

