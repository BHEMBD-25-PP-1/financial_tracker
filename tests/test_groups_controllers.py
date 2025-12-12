"""Тесты для Groups API контроллеров."""

from unittest.mock import MagicMock, patch
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.dependencies import get_current_user, get_db
from app.db.models import User as DBUser, Group, GroupRole as DBGroupRole, UserGroup
from app.groups.models import GroupRole


@pytest.fixture
def mock_db_user():
    """Мок пользователя."""
    user = MagicMock(unsafe_spec=DBUser)
    user.id = 1
    user.first_name = "Test"
    user.last_name = "User"
    user.login = "test_user"
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
    app.dependency_overrides.clear()


@patch('app.groups.controllers.GroupRepository')
def test_get_groups_success(mock_repo_class, client_with_auth, mock_db_user):
    """Тест успешного получения списка групп."""
    mock_repo = MagicMock()
    mock_repo_class.return_value = mock_repo
    
    mock_group1 = MagicMock()
    mock_group1.id = 1
    mock_group1.name = "Group 1"
    mock_group1.owner_id = 1
    mock_group1.created_at = datetime(2024, 1, 15, 10, 0, 0)
    mock_group1.updated_at = datetime(2024, 1, 15, 10, 0, 0)
    
    mock_group2 = MagicMock()
    mock_group2.id = 2
    mock_group2.name = "Group 2"
    mock_group2.owner_id = 1
    mock_group2.created_at = datetime(2024, 1, 15, 10, 0, 0)
    mock_group2.updated_at = datetime(2024, 1, 15, 10, 0, 0)
    
    mock_repo.get_by_user_id.return_value = ([mock_group1, mock_group2], 2)
    
    response = client_with_auth.get("/api/v1/groups?page=1&size=20")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["size"] == 20


@patch('app.groups.controllers.GroupRepository')
def test_create_group_success(mock_repo_class, client_with_auth, mock_db_user):
    """Тест успешного создания группы."""
    mock_repo = MagicMock()
    mock_repo_class.return_value = mock_repo
    
    mock_group = MagicMock()
    mock_group.id = 1
    mock_group.name = "New Group"
    mock_group.owner_id = 1
    mock_group.created_at = datetime(2024, 1, 15, 10, 0, 0)
    mock_group.updated_at = datetime(2024, 1, 15, 10, 0, 0)
    
    mock_repo.create.return_value = mock_group
    
    response = client_with_auth.post(
        "/api/v1/groups",
        json={"name": "New Group", "owner_id": 1}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "New Group"


@patch('app.groups.controllers.GroupRepository')
def test_create_group_validation_error(mock_repo_class, client_with_auth):
    """Тест создания группы с ошибкой валидации."""
    mock_repo = MagicMock()
    mock_repo_class.return_value = mock_repo
    mock_repo.create.side_effect = ValueError("Group name cannot be empty")
    
    # Пустое имя валидируется Pydantic и возвращает 422
    response = client_with_auth.post(
        "/api/v1/groups",
        json={"name": "", "owner_id": 1}
    )
    
    # Pydantic валидация возвращает 422, а ValueError из репозитория - 400
    assert response.status_code in [400, 422]
    
    # Тест с валидным JSON, но ошибкой в репозитории
    response = client_with_auth.post(
        "/api/v1/groups",
        json={"name": "Valid Name", "owner_id": 1}
    )
    # Если репозиторий выбрасывает ValueError, должен быть 400
    if mock_repo.create.called:
        assert response.status_code == 400


@patch('app.groups.controllers.GroupRepository')
def test_get_group_by_id_success(mock_repo_class, client_with_auth, mock_db_user):
    """Тест успешного получения группы по ID."""
    mock_repo = MagicMock()
    mock_repo_class.return_value = mock_repo
    
    mock_group = MagicMock()
    mock_group.id = 1
    mock_group.name = "Test Group"
    mock_group.owner_id = 1
    mock_group.created_at = datetime(2024, 1, 15, 10, 0, 0)
    mock_group.updated_at = datetime(2024, 1, 15, 10, 0, 0)
    
    mock_repo.get_by_id.return_value = mock_group
    mock_repo.is_member.return_value = True
    
    response = client_with_auth.get("/api/v1/groups/1")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "Test Group"


@patch('app.groups.controllers.GroupRepository')
def test_get_group_by_id_not_found(mock_repo_class, client_with_auth):
    """Тест получения несуществующей группы."""
    mock_repo = MagicMock()
    mock_repo_class.return_value = mock_repo
    mock_repo.get_by_id.return_value = None
    
    response = client_with_auth.get("/api/v1/groups/99999")
    
    assert response.status_code == 404


@patch('app.groups.controllers.GroupRepository')
def test_get_group_by_id_forbidden(mock_repo_class, client_with_auth):
    """Тест получения группы без доступа."""
    mock_repo = MagicMock()
    mock_repo_class.return_value = mock_repo
    
    mock_group = MagicMock()
    mock_group.id = 1
    mock_group.name = "Test Group"
    mock_group.owner_id = 1
    mock_group.created_at = datetime(2024, 1, 15, 10, 0, 0)
    mock_group.updated_at = datetime(2024, 1, 15, 10, 0, 0)
    
    mock_repo.get_by_id.return_value = mock_group
    mock_repo.is_member.return_value = False
    
    response = client_with_auth.get("/api/v1/groups/1")
    
    assert response.status_code == 403


@patch('app.groups.controllers.GroupRepository')
def test_update_group_success(mock_repo_class, client_with_auth):
    """Тест успешного обновления группы."""
    mock_repo = MagicMock()
    mock_repo_class.return_value = mock_repo
    
    updated_group = MagicMock()
    updated_group.id = 1
    updated_group.name = "Updated Group"
    updated_group.owner_id = 1
    updated_group.created_at = datetime(2024, 1, 15, 10, 0, 0)
    updated_group.updated_at = datetime(2024, 1, 15, 10, 0, 0)
    
    mock_repo.update.return_value = updated_group
    
    response = client_with_auth.put(
        "/api/v1/groups/1",
        json={"name": "Updated Group"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Group"


@patch('app.groups.controllers.GroupRepository')
def test_update_group_not_found(mock_repo_class, client_with_auth):
    """Тест обновления несуществующей группы."""
    mock_repo = MagicMock()
    mock_repo_class.return_value = mock_repo
    mock_repo.update.return_value = None
    
    response = client_with_auth.put(
        "/api/v1/groups/99999",
        json={"name": "Updated Group"}
    )
    
    assert response.status_code == 404


@patch('app.groups.controllers.GroupRepository')
def test_delete_group_success(mock_repo_class, client_with_auth):
    """Тест успешного удаления группы."""
    mock_repo = MagicMock()
    mock_repo_class.return_value = mock_repo
    mock_repo.delete.return_value = True
    
    response = client_with_auth.delete("/api/v1/groups/1")
    
    assert response.status_code == 204


@patch('app.groups.controllers.GroupRepository')
def test_delete_group_not_found(mock_repo_class, client_with_auth):
    """Тест удаления несуществующей группы."""
    mock_repo = MagicMock()
    mock_repo_class.return_value = mock_repo
    mock_repo.delete.return_value = False
    
    response = client_with_auth.delete("/api/v1/groups/99999")
    
    assert response.status_code == 404


@patch('app.groups.controllers.GroupRepository')
def test_get_group_members_success(mock_repo_class, client_with_auth):
    """Тест успешного получения участников группы."""
    mock_repo = MagicMock()
    mock_repo_class.return_value = mock_repo
    mock_repo.is_member.return_value = True
    
    mock_member = MagicMock()
    mock_member.id = 1
    mock_member.user_id = 2
    mock_member.group_id = 1
    mock_member.role = DBGroupRole.MEMBER
    mock_member.joined_at = datetime(2024, 1, 15, 10, 0, 0)
    mock_member.user = None
    
    mock_repo.get_members.return_value = [mock_member]
    
    response = client_with_auth.get("/api/v1/groups/1/members")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["members"]) == 1
    assert data["members"][0]["user_id"] == 2


@patch('app.groups.controllers.GroupRepository')
def test_get_group_members_forbidden(mock_repo_class, client_with_auth):
    """Тест получения участников без доступа."""
    mock_repo = MagicMock()
    mock_repo_class.return_value = mock_repo
    mock_repo.is_member.return_value = False
    
    response = client_with_auth.get("/api/v1/groups/1/members")
    
    assert response.status_code == 403


@patch('app.groups.controllers.GroupRepository')
@patch('app.groups.controllers.UserRepository')
def test_add_group_member_success(mock_user_repo_class, mock_repo_class, client_with_auth):
    """Тест успешного добавления участника."""
    mock_repo = MagicMock()
    mock_repo_class.return_value = mock_repo
    
    mock_user_group = MagicMock()
    mock_user_group.id = 1
    mock_user_group.user_id = 2
    mock_user_group.group_id = 1
    mock_user_group.role = DBGroupRole.MEMBER
    mock_user_group.joined_at = datetime(2024, 1, 15, 10, 0, 0)
    
    mock_repo.add_member.return_value = mock_user_group
    
    mock_user_repo = MagicMock()
    mock_user_repo_class.return_value = mock_user_repo
    
    mock_user = MagicMock()
    mock_user.id = 2
    mock_user.first_name = "Test2"
    mock_user.last_name = "User2"
    mock_user.login = "test_user2"
    mock_user_repo.get_by_id.return_value = mock_user
    
    response = client_with_auth.post(
        "/api/v1/groups/1/members",
        json={"user_id": 2}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == 2
    assert data["group_id"] == 1


@patch('app.groups.controllers.GroupRepository')
def test_add_group_member_validation_error(mock_repo_class, client_with_auth):
    """Тест добавления участника с ошибкой валидации."""
    mock_repo = MagicMock()
    mock_repo_class.return_value = mock_repo
    mock_repo.add_member.side_effect = ValueError("Group with ID 1 not found")
    
    response = client_with_auth.post(
        "/api/v1/groups/1/members",
        json={"user_id": 2}
    )
    
    assert response.status_code == 400


@patch('app.groups.controllers.GroupRepository')
def test_remove_group_member_success(mock_repo_class, client_with_auth):
    """Тест успешного удаления участника."""
    mock_repo = MagicMock()
    mock_repo_class.return_value = mock_repo
    mock_repo.remove_member.return_value = True
    
    response = client_with_auth.delete("/api/v1/groups/1/members/2")
    
    assert response.status_code == 204


@patch('app.groups.controllers.GroupRepository')
def test_remove_group_member_not_found(mock_repo_class, client_with_auth):
    """Тест удаления несуществующего участника."""
    mock_repo = MagicMock()
    mock_repo_class.return_value = mock_repo
    mock_repo.remove_member.return_value = False
    
    response = client_with_auth.delete("/api/v1/groups/1/members/99999")
    
    assert response.status_code == 404


@patch('app.groups.controllers.GroupRepository')
@patch('app.groups.controllers.TransactionRepository')
def test_get_group_analytics_success(mock_trans_repo_class, mock_repo_class, client_with_auth):
    """Тест успешного получения аналитики группы."""
    mock_repo = MagicMock()
    mock_repo_class.return_value = mock_repo
    mock_repo.is_member.return_value = True
    
    mock_trans_repo = MagicMock()
    mock_trans_repo_class.return_value = mock_trans_repo
    
    from app.db.models import TransactionType
    
    mock_trans = MagicMock()
    mock_trans.type = TransactionType.EXPENSE
    mock_trans.amount = 1000.0
    mock_trans.category = "Еда"
    mock_trans.date = None
    
    mock_trans_repo.get_all.return_value = ([mock_trans], 1)
    
    response = client_with_auth.get("/api/v1/groups/1/analytics")
    
    assert response.status_code == 200
    data = response.json()
    assert data["group_id"] == 1
    assert data["total_expense"] == 1000.0


@patch('app.groups.controllers.GroupRepository')
def test_get_group_analytics_forbidden(mock_repo_class, client_with_auth):
    """Тест получения аналитики без доступа."""
    mock_repo = MagicMock()
    mock_repo_class.return_value = mock_repo
    mock_repo.is_member.return_value = False
    
    response = client_with_auth.get("/api/v1/groups/1/analytics")
    
    assert response.status_code == 403
