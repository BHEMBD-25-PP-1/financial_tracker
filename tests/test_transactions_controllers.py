"""Тесты для контроллеров транзакций."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import date, datetime

from main import app
from app.core.dependencies import get_current_user, get_db
from app.transactions.models import Transaction, TransactionType, TransactionCategory


# Мокаем текущего пользователя
class MockUser:
    id = 1

mock_user = MockUser()

# Переопределяем зависимости FastAPI
app.dependency_overrides[get_current_user] = lambda: mock_user
app.dependency_overrides[get_db] = lambda: MagicMock()

client = TestClient(app)


@pytest.fixture
def mock_transaction():
    """Мок транзакции."""
    return Transaction(
        id=1,
        name="Покупка продуктов",
        type=TransactionType.EXPENSE,
        category="Еда",
        amount=1000.0,
        date=date(2024, 1, 15),
        user_id=1,
        group_id=None,
        created_at=datetime(2024, 1, 15, 10, 0, 0),
        updated_at=datetime(2024, 1, 15, 10, 0, 0)
    )


@pytest.fixture
def mock_transactions():
    """Мок списка транзакций."""
    return [
        Transaction(
            id=1,
            name="Покупка продуктов",
            type=TransactionType.EXPENSE,
            category="Еда",
            amount=1000.0,
            date=date(2024, 1, 15),
            user_id=1,
            group_id=None,
            created_at=datetime(2024, 1, 15, 10, 0, 0),
            updated_at=datetime(2024, 1, 15, 10, 0, 0)
        ),
        Transaction(
            id=2,
            name="Зарплата",
            type=TransactionType.INCOME,
            category="Работа",
            amount=50000.0,
            date=date(2024, 1, 1),
            user_id=1,
            group_id=None,
            created_at=datetime(2024, 1, 1, 10, 0, 0),
            updated_at=datetime(2024, 1, 1, 10, 0, 0)
        ),
    ]


@patch("app.transactions.controllers.TransactionService")
def test_get_transactions_success(mock_service_class, mock_transactions):
    """Тест успешного получения списка транзакций."""
    mock_service = MagicMock()
    mock_service.get_transactions.return_value = (mock_transactions, 2)
    mock_service_class.return_value = mock_service

    response = client.get("/api/v1/transactions?page=1&size=20")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert data["page"] == 1
    assert data["size"] == 20
    assert len(data["items"]) == 2
    assert data["items"][0]["id"] == 1
    assert data["items"][0]["name"] == "Покупка продуктов"


@patch("app.transactions.controllers.TransactionService")
def test_get_transactions_with_filters(mock_service_class, mock_transactions):
    """Тест получения транзакций с фильтрами."""
    mock_service = MagicMock()
    mock_service.get_transactions.return_value = ([mock_transactions[0]], 1)
    mock_service_class.return_value = mock_service

    response = client.get(
        "/api/v1/transactions?page=1&size=20"
        "&category=Еда&transaction_type=expense&start_date=2024-01-01&end_date=2024-12-31"
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1


@patch("app.transactions.controllers.TransactionService")
def test_get_transactions_error(mock_service_class):
    """Тест обработки ошибки при получении транзакций."""
    mock_service = MagicMock()
    mock_service.get_transactions.side_effect = Exception("Database error")
    mock_service_class.return_value = mock_service

    response = client.get("/api/v1/transactions")
    
    assert response.status_code == 500
    assert "Ошибка при получении транзакций" in response.json()["detail"]


@patch("app.transactions.controllers.TransactionService")
def test_create_transaction_success(mock_service_class, mock_transaction):
    """Тест успешного создания транзакции."""
    mock_service = MagicMock()
    mock_service.create_transaction.return_value = mock_transaction
    mock_service_class.return_value = mock_service

    response = client.post(
        "/api/v1/transactions",
        json={
            "name": "Покупка продуктов",
            "type": "expense",
            "category": "Еда",
            "amount": 1000.0,
            "date": "2024-01-15"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "Покупка продуктов"
    assert data["type"] == "expense"
    assert data["category"] == "Еда"
    assert data["amount"] == 1000.0


@patch("app.transactions.controllers.TransactionService")
def test_create_transaction_validation_error(mock_service_class):
    """Тест обработки ошибки валидации при создании транзакции."""
    mock_service = MagicMock()
    mock_service.create_transaction.side_effect = ValueError("Недопустимая категория")
    mock_service_class.return_value = mock_service

    response = client.post(
        "/api/v1/transactions",
        json={
            "name": "Покупка",
            "type": "expense",
            "category": "Несуществующая категория",
            "amount": 1000.0,
            "date": "2024-01-15"
        }
    )
    
    assert response.status_code == 400
    assert "Недопустимая категория" in response.json()["detail"]


@patch("app.transactions.controllers.TransactionService")
def test_get_transaction_by_id_success(mock_service_class, mock_transaction):
    """Тест успешного получения транзакции по ID."""
    mock_service = MagicMock()
    mock_service.get_transaction_by_id.return_value = mock_transaction
    mock_service_class.return_value = mock_service

    response = client.get("/api/v1/transactions/1")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "Покупка продуктов"


@patch("app.transactions.controllers.TransactionService")
def test_get_transaction_by_id_not_found(mock_service_class):
    """Тест получения несуществующей транзакции."""
    mock_service = MagicMock()
    mock_service.get_transaction_by_id.return_value = None
    mock_service_class.return_value = mock_service

    response = client.get("/api/v1/transactions/999")
    
    assert response.status_code == 404
    assert "не найдена" in response.json()["detail"]


@patch("app.transactions.controllers.TransactionService")
def test_update_transaction_success(mock_service_class, mock_transaction):
    """Тест успешного обновления транзакции."""
    updated_transaction = Transaction(
        id=1,
        name="Обновленная покупка",
        type=TransactionType.EXPENSE,
        category="Еда",
        amount=1500.0,
        date=date(2024, 1, 15),
        user_id=1,
        group_id=None,
        created_at=datetime(2024, 1, 15, 10, 0, 0),
        updated_at=datetime(2024, 1, 15, 11, 0, 0)
    )
    
    mock_service = MagicMock()
    mock_service.update_transaction.return_value = updated_transaction
    mock_service_class.return_value = mock_service

    response = client.put(
        "/api/v1/transactions/1",
        json={
            "name": "Обновленная покупка",
            "amount": 1500.0
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "Обновленная покупка"
    assert data["amount"] == 1500.0


@patch("app.transactions.controllers.TransactionService")
def test_update_transaction_not_found(mock_service_class):
    """Тест обновления несуществующей транзакции."""
    mock_service = MagicMock()
    mock_service.update_transaction.return_value = None
    mock_service_class.return_value = mock_service

    response = client.put(
        "/api/v1/transactions/999",
        json={"name": "Обновленная покупка"}
    )
    
    assert response.status_code == 404
    assert "не найдена" in response.json()["detail"]


@patch("app.transactions.controllers.TransactionService")
def test_update_transaction_validation_error(mock_service_class):
    """Тест обработки ошибки валидации при обновлении транзакции."""
    mock_service = MagicMock()
    mock_service.update_transaction.side_effect = ValueError("Transaction amount must be positive")
    mock_service_class.return_value = mock_service

    response = client.put(
        "/api/v1/transactions/1",
        json={"amount": -100}
    )
    
    assert response.status_code == 400
    assert "must be positive" in response.json()["detail"]


@patch("app.transactions.controllers.TransactionService")
def test_delete_transaction_success(mock_service_class):
    """Тест успешного удаления транзакции."""
    mock_service = MagicMock()
    mock_service.delete_transaction.return_value = True
    mock_service_class.return_value = mock_service

    response = client.delete("/api/v1/transactions/1")
    
    assert response.status_code == 204


@patch("app.transactions.controllers.TransactionService")
def test_delete_transaction_not_found(mock_service_class):
    """Тест удаления несуществующей транзакции."""
    mock_service = MagicMock()
    mock_service.delete_transaction.return_value = False
    mock_service_class.return_value = mock_service

    response = client.delete("/api/v1/transactions/999")
    
    assert response.status_code == 404
    assert "не найдена" in response.json()["detail"]

