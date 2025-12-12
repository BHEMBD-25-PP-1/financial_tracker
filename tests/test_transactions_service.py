"""Тесты для сервиса транзакций."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import date, datetime

from app.transactions.service import TransactionService
from app.transactions.models import TransactionType, TransactionCategory
from app.db.models import Transaction as DBTransaction, TransactionType as DBTransactionType


@pytest.fixture
def mock_db_session():
    """Мок сессии базы данных."""
    return MagicMock()


@pytest.fixture
def mock_repository():
    """Мок репозитория транзакций."""
    return MagicMock()


@pytest.fixture
def service(mock_db_session, mock_repository):
    """Фикстура для создания сервиса с мок-репозиторием."""
    with patch("app.transactions.service.TransactionRepository", return_value=mock_repository):
        service = TransactionService(mock_db_session)
        service.transaction_repository = mock_repository
        return service


@pytest.fixture
def db_transaction():
    """Мок транзакции из БД."""
    transaction = MagicMock(spec=DBTransaction)
    transaction.id = 1
    transaction.name = "Покупка продуктов"
    transaction.type = DBTransactionType.EXPENSE
    transaction.category = "Еда"
    transaction.amount = 1000.0
    transaction.date = date(2024, 1, 15)
    transaction.user_id = 1
    transaction.group_id = None
    transaction.created_at = datetime(2024, 1, 15, 10, 0, 0)
    transaction.updated_at = datetime(2024, 1, 15, 10, 0, 0)
    return transaction


def test_get_transactions_success(service, mock_repository, db_transaction):
    """Тест успешного получения списка транзакций."""
    mock_repository.get_all.return_value = ([db_transaction], 1)

    transactions, total = service.get_transactions(
        user_id=1,
        page=1,
        size=20
    )

    assert total == 1
    assert len(transactions) == 1
    assert transactions[0].id == 1
    assert transactions[0].name == "Покупка продуктов"
    assert transactions[0].type == TransactionType.EXPENSE
    assert transactions[0].category == TransactionCategory.FOOD


def test_get_transactions_with_filters(service, mock_repository, db_transaction):
    """Тест получения транзакций с фильтрами."""
    mock_repository.get_all.return_value = ([db_transaction], 1)

    transactions, total = service.get_transactions(
        user_id=1,
        page=1,
        size=20,
        category=TransactionCategory.FOOD,
        transaction_type=TransactionType.EXPENSE,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31)
    )

    assert total == 1
    mock_repository.get_all.assert_called_once()
    call_args = mock_repository.get_all.call_args
    assert call_args[1]["category"] == "Еда"
    assert call_args[1]["transaction_type"] == DBTransactionType.EXPENSE


def test_create_transaction_success(service, mock_repository, db_transaction):
    """Тест успешного создания транзакции."""
    mock_repository.create.return_value = db_transaction

    transaction = service.create_transaction(
        name="Покупка продуктов",
        transaction_type=TransactionType.EXPENSE,
        category="Еда",
        amount=1000.0,
        transaction_date=date(2024, 1, 15),
        user_id=1
    )

    assert transaction.id == 1
    assert transaction.name == "Покупка продуктов"
    assert transaction.type == TransactionType.EXPENSE
    assert transaction.category == TransactionCategory.FOOD
    assert transaction.amount == 1000.0
    mock_repository.create.assert_called_once()


def test_create_transaction_invalid_category(service, mock_repository):
    """Тест создания транзакции с недопустимой категорией."""
    with pytest.raises(ValueError, match="Недопустимая категория"):
        service.create_transaction(
            name="Покупка",
            transaction_type=TransactionType.EXPENSE,
            category="Несуществующая категория",
            amount=1000.0,
            transaction_date=date(2024, 1, 15),
            user_id=1
        )


def test_get_transaction_by_id_success(service, mock_repository, db_transaction):
    """Тест успешного получения транзакции по ID."""
    mock_repository.get_by_id.return_value = db_transaction

    transaction = service.get_transaction_by_id(transaction_id=1, user_id=1)

    assert transaction is not None
    assert transaction.id == 1
    assert transaction.name == "Покупка продуктов"
    mock_repository.get_by_id.assert_called_once_with(1, user_id=1)


def test_get_transaction_by_id_not_found(service, mock_repository):
    """Тест получения несуществующей транзакции."""
    mock_repository.get_by_id.return_value = None

    transaction = service.get_transaction_by_id(transaction_id=999, user_id=1)

    assert transaction is None


def test_update_transaction_success(service, mock_repository, db_transaction):
    """Тест успешного обновления транзакции."""
    updated_db_transaction = MagicMock(spec=DBTransaction)
    updated_db_transaction.id = 1
    updated_db_transaction.name = "Обновленная покупка"
    updated_db_transaction.type = DBTransactionType.EXPENSE
    updated_db_transaction.category = "Еда"
    updated_db_transaction.amount = 1500.0
    updated_db_transaction.date = date(2024, 1, 15)
    updated_db_transaction.user_id = 1
    updated_db_transaction.group_id = None
    updated_db_transaction.created_at = datetime(2024, 1, 15, 10, 0, 0)
    updated_db_transaction.updated_at = datetime(2024, 1, 15, 11, 0, 0)

    mock_repository.update.return_value = updated_db_transaction

    transaction = service.update_transaction(
        transaction_id=1,
        user_id=1,
        name="Обновленная покупка",
        amount=1500.0
    )

    assert transaction is not None
    assert transaction.name == "Обновленная покупка"
    assert transaction.amount == 1500.0
    mock_repository.update.assert_called_once()


def test_update_transaction_not_found(service, mock_repository):
    """Тест обновления несуществующей транзакции."""
    mock_repository.update.return_value = None

    transaction = service.update_transaction(
        transaction_id=999,
        user_id=1,
        name="Обновленная покупка"
    )

    assert transaction is None


def test_update_transaction_with_string_category(service, mock_repository, db_transaction):
    """Тест обновления транзакции со строковой категорией."""
    mock_repository.update.return_value = db_transaction

    transaction = service.update_transaction(
        transaction_id=1,
        user_id=1,
        category="Еда"
    )

    assert transaction is not None
    mock_repository.update.assert_called_once()
    call_args = mock_repository.update.call_args
    assert call_args[1]["category"] == "Еда"


def test_update_transaction_invalid_category(service, mock_repository):
    """Тест обновления транзакции с недопустимой категорией."""
    with pytest.raises(ValueError, match="Недопустимая категория"):
        service.update_transaction(
            transaction_id=1,
            user_id=1,
            category="Несуществующая категория"
        )


def test_delete_transaction_success(service, mock_repository):
    """Тест успешного удаления транзакции."""
    mock_repository.delete.return_value = True

    result = service.delete_transaction(transaction_id=1, user_id=1)

    assert result is True
    mock_repository.delete.assert_called_once_with(1, 1)


def test_delete_transaction_not_found(service, mock_repository):
    """Тест удаления несуществующей транзакции."""
    mock_repository.delete.return_value = False

    result = service.delete_transaction(transaction_id=999, user_id=1)

    assert result is False


def test_convert_db_transaction_to_model(service, db_transaction):
    """Тест преобразования транзакции из БД в модель API."""
    transaction = service._convert_db_transaction_to_model(db_transaction)

    assert transaction.id == 1
    assert transaction.name == "Покупка продуктов"
    assert transaction.type == TransactionType.EXPENSE
    assert transaction.category == TransactionCategory.FOOD
    assert transaction.amount == 1000.0
    assert transaction.date == date(2024, 1, 15)
    assert transaction.user_id == 1
    assert transaction.group_id is None

