import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import date

from main import app
from app.db.models import Transaction, TransactionType
from app.core.dependencies import get_current_user, get_db

# Мокаем текущего пользователя
class MockUser:
    id = 1

mock_user = MockUser()

# Переопределяем зависимости FastAPI
app.dependency_overrides[get_current_user] = lambda: mock_user
app.dependency_overrides[get_db] = lambda: MagicMock()

client = TestClient(app)

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

def test_get_summary(mock_repo):
    response = client.get("/api/v1/analytics/summary")  # <- полный путь
    assert response.status_code == 200

    data = response.json()
    assert data["total_income"] == 300.0
    assert data["total_expense"] == 50.0
    assert data["balance"] == 250.0
    assert data["transaction_count"] == 3
    assert data["period"] is None

def test_get_summary_with_dates(mock_repo):
    response = client.get("/api/v1/analytics/summary?start_date=2025-01-01&end_date=2025-12-31")  # <- полный путь
    assert response.status_code == 200

    data = response.json()
    assert data["period"]["start_date"] == "2025-01-01"
    assert data["period"]["end_date"] == "2025-12-31"



class MockUser:
    id = 1


mock_user = MockUser()

# Переопределяем зависимости FastAPI
app.dependency_overrides[get_current_user] = lambda: mock_user
app.dependency_overrides[get_db] = lambda: MagicMock()

client = TestClient(app)

# Общий набор мок-транзакций
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


# Тест для /by-category
def test_get_by_category(mock_repo):
    response = client.get("/api/v1/analytics/by-category")
    assert response.status_code == 200

    data = response.json()
    categories = {c["category"]: c for c in data["categories"]}

    # Проверяем сумму и количество по категории "Job"
    assert categories["Job"]["total_amount"] == 300.0
    assert categories["Job"]["transaction_count"] == 2
    assert categories["Job"]["transaction_type"] == "income"

    # Проверяем сумму и количество по категории "Food"
    assert categories["Food"]["total_amount"] == 50.0
    assert categories["Food"]["transaction_count"] == 1
    assert categories["Food"]["transaction_type"] == "expense"

    assert data["period"] is None


def test_get_by_category_with_dates(mock_repo):
    response = client.get("/api/v1/analytics/by-category?start_date=2025-01-01&end_date=2025-12-31")
    assert response.status_code == 200

    data = response.json()
    assert data["period"]["start_date"] == "2025-01-01"
    assert data["period"]["end_date"] == "2025-12-31"


# Тест для /by-period
def test_get_by_period(mock_repo):
    response = client.get("/api/v1/analytics/by-period?start_date=2025-01-01&end_date=2025-01-31")
    assert response.status_code == 200

    data = response.json()
    assert data["period_type"] == "month"
    assert len(data["periods"]) > 0

    # Проверяем суммарный доход и расход за период
    total_income = sum(p["total_income"] for p in data["periods"])
    total_expense = sum(p["total_expense"] for p in data["periods"])

    assert total_income == 300.0
    assert total_expense == 50.0


# Тест для /trends
def test_get_trends(mock_repo):
    response = client.get("/api/v1/analytics/trends?start_date=2025-01-01&end_date=2025-01-31")
    assert response.status_code == 200

    data = response.json()

    # Проверяем, что доход и расход посчитаны
    assert data["income_trend"]["average_daily"] > 0
    assert data["expense_trend"]["average_daily"] > 0

    # Проверяем направление трендов (только для корректности структуры)
    assert data["income_trend"]["direction"] in ["up", "down", "stable"]
    assert data["expense_trend"]["direction"] in ["up", "down", "stable"]

    # Проверяем период
    assert data["period"]["start_date"] == "2025-01-01"
    assert data["period"]["end_date"] == "2025-01-31"