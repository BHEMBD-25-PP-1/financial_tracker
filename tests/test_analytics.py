import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import date

from main import app
from app.db.models import Transaction, TransactionType, User as DBUser
from app.core.dependencies import get_current_user, get_db


@pytest.fixture
def mock_db_user():
    """Мок пользователя из базы данных."""
    user = MagicMock(spec=DBUser)
    user.id = 1
    return user


@pytest.fixture
def client_with_auth(mock_db_user):
    """TestClient с переопределёнными зависимостями для авторизации."""
    app.dependency_overrides[get_current_user] = lambda: mock_db_user
    app.dependency_overrides[get_db] = lambda: MagicMock()
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

# Мокаем транзакции
mock_transactions = [
    Transaction(
        id=1,
        user_id=1,
        amount=100.0,
        type=TransactionType.INCOME,
        name="Salary",
        category="Job",
        date=date(2025, 1, 1),
        group_id=None
    ),
    Transaction(
        id=2,
        user_id=1,
        amount=50.0,
        type=TransactionType.EXPENSE,
        name="Groceries",
        category="Food",
        date=date(2025, 1, 2),
        group_id=None
    ),
    Transaction(
        id=3,
        user_id=1,
        amount=200.0,
        type=TransactionType.INCOME,
        name="Freelance",
        category="Job",
        date=date(2025, 1, 3),
        group_id=None
    ),
]

@pytest.fixture
def mock_repo():
    """Мок репозитория TransactionRepository.get_all"""
    with patch("app.repositories.transaction_repository.TransactionRepository.get_all") as mock:
        mock.return_value = (mock_transactions, len(mock_transactions))
        yield mock

def test_get_summary(mock_repo, client_with_auth):
    response = client_with_auth.get("/api/v1/analytics/summary")
    assert response.status_code == 200

    data = response.json()
    assert data["total_income"] == 300.0
    assert data["total_expense"] == 50.0
    assert data["balance"] == 250.0
    assert data["transaction_count"] == 3
    assert data["period"] is None


def test_get_by_category(mock_repo, client_with_auth):
    response = client_with_auth.get("/api/v1/analytics/by-category")
    assert response.status_code == 200

    data = response.json()
    categories = {c["category"]: c for c in data["categories"]}

    # Проверяем сумму и количество по категории "Job"
    assert categories["Job"]["total_amount"] == 300.0
    assert categories["Job"]["transaction_count"] == 2
    assert categories["Job"]["transaction_type"] == "INCOME"

    # Проверяем сумму и количество по категории "Food"
    assert categories["Food"]["total_amount"] == 50.0
    assert categories["Food"]["transaction_count"] == 1
    assert categories["Food"]["transaction_type"] == "EXPENSE"

    assert data["period"] is None

    response_with_dates = client_with_auth.get("/api/v1/analytics/by-category?start_date=2025-01-01&end_date=2025-12-31")
    assert response_with_dates.status_code == 200
    data_with_dates = response_with_dates.json()
    assert data_with_dates["period"]["start_date"] == "2025-01-01"
    assert data_with_dates["period"]["end_date"] == "2025-12-31"


def test_get_by_period(mock_repo, client_with_auth):
    response = client_with_auth.get("/api/v1/analytics/by-period?start_date=2025-01-01&end_date=2025-01-31")
    assert response.status_code == 200

    data = response.json()
    assert data["period_type"] == "MONTH"
    assert len(data["periods"]) > 0

    # Проверяем суммарный доход и расход за период
    total_income = sum(p["total_income"] for p in data["periods"])
    total_expense = sum(p["total_expense"] for p in data["periods"])

    assert total_income == 300.0
    assert total_expense == 50.0


def test_get_trends(mock_repo, client_with_auth):
    response = client_with_auth.get("/api/v1/analytics/trends?start_date=2025-01-01&end_date=2025-01-31")
    assert response.status_code == 200

    data = response.json()

    # Проверяем, что доход и расход посчитаны
    assert data["income_trend"]["average_daily"] > 0
    assert data["expense_trend"]["average_daily"] > 0

    # Проверяем направление трендов (только для корректности структуры)
    assert data["income_trend"]["direction"] in ["UP", "DOWN", "STABLE"]
    assert data["expense_trend"]["direction"] in ["UP", "DOWN", "STABLE"]

    # Проверяем период
    assert data["period"]["start_date"] == "2025-01-01"
    assert data["period"]["end_date"] == "2025-01-31"