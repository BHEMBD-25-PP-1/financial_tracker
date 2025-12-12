"""Тесты для TransactionRepository."""

import sys
from pathlib import Path

import pytest
from datetime import date
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

# Ensure project modules are importable when running pytest from repo root
PROJECT_ROOT = Path(__file__).resolve().parents[0]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db.session import SessionLocal, engine
from app.db.base import Base
from app.db.models import Transaction, User, Group, TransactionType
from app.repositories.transaction_repository import TransactionRepository


def _clean_transactions_table():
    """Вспомогательная функция для очистки таблицы транзакций."""
    session = SessionLocal()
    try:
        # Удаляем транзакции перед удалением пользователей и групп
        session.query(Transaction).delete()
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@pytest.fixture(scope="module", autouse=True)
def ensure_tables():
    """Создание таблиц перед всеми тестами."""
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture(autouse=True)
def clean_transactions_table():
    """Очистка таблицы транзакций перед и после каждого теста."""
    _clean_transactions_table()
    yield
    _clean_transactions_table()


@pytest.fixture
def test_user():
    """Создание тестового пользователя."""
    from app.repositories.user_repository import UserRepository
    
    session = SessionLocal()
    try:
        # Проверяем, существует ли пользователь
        existing_user = session.query(User).filter(User.login == "test_user").first()
        if existing_user:
            yield existing_user
        else:
            user_repo = UserRepository(db_session=session)
            user = user_repo.add(
                first_name="Test",
                last_name="User",
                login="test_user",
                password="testpassword123"
            )
            session.commit()
            session.refresh(user)
            yield user
            # Удаляем только если мы его создали
            session.delete(user)
            session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@pytest.fixture
def test_group(test_user):
    """Создание тестовой группы."""
    session = SessionLocal()
    try:
        group = Group(
            name="Test Group",
            owner_id=test_user.id
        )
        session.add(group)
        session.commit()
        session.refresh(group)
        yield group
        session.delete(group)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@pytest.fixture
def repo():
    """Фикстура для создания репозитория."""
    with TransactionRepository() as repository:
        yield repository


def test_create_transaction_success(repo, test_user):
    """Тест создания транзакции и сохранения в БД."""
    transaction = repo.create(
        name="Покупка продуктов",
        type=TransactionType.EXPENSE,
        category="Еда",
        amount=1000.0,
        transaction_date=date(2024, 1, 15),
        user_id=test_user.id
    )

    assert transaction.id is not None
    assert transaction.name == "Покупка продуктов"
    assert transaction.type == TransactionType.EXPENSE
    assert transaction.category == "Еда"
    assert transaction.amount == 1000.0
    assert transaction.user_id == test_user.id

    # Проверяем, что транзакция сохранена в БД
    session = SessionLocal()
    try:
        db_transaction = session.query(Transaction).filter_by(id=transaction.id).one()
        assert db_transaction.name == "Покупка продуктов"
        assert db_transaction.amount == 1000.0
    finally:
        session.close()


def test_create_transaction_with_group(repo, test_user, test_group):
    """Тест создания транзакции с группой."""
    transaction = repo.create(
        name="Групповая покупка",
        type=TransactionType.EXPENSE,
        category="Еда",
        amount=2000.0,
        transaction_date=date(2024, 1, 15),
        user_id=test_user.id,
        group_id=test_group.id
    )

    assert transaction.group_id == test_group.id


def test_create_transaction_invalid_user(repo):
    """Тест создания транзакции с несуществующим пользователем."""
    with pytest.raises(ValueError, match="User with ID.*not found"):
        repo.create(
            name="Покупка",
            type=TransactionType.EXPENSE,
            category="Еда",
            amount=1000.0,
            transaction_date=date(2024, 1, 15),
            user_id=99999
        )


def test_create_transaction_invalid_group(repo, test_user):
    """Тест создания транзакции с несуществующей группой."""
    with pytest.raises(ValueError, match="Group with ID.*not found"):
        repo.create(
            name="Покупка",
            type=TransactionType.EXPENSE,
            category="Еда",
            amount=1000.0,
            transaction_date=date(2024, 1, 15),
            user_id=test_user.id,
            group_id=99999
        )


def test_create_transaction_validation_errors(repo, test_user):
    """Тест валидации данных при создании транзакции."""
    # Пустое имя
    with pytest.raises(ValueError, match="Transaction name cannot be empty"):
        repo.create(
            name="",
            type=TransactionType.EXPENSE,
            category="Еда",
            amount=1000.0,
            transaction_date=date(2024, 1, 15),
            user_id=test_user.id
        )

    # Отрицательная сумма
    with pytest.raises(ValueError, match="Transaction amount must be positive"):
        repo.create(
            name="Покупка",
            type=TransactionType.EXPENSE,
            category="Еда",
            amount=-100.0,
            transaction_date=date(2024, 1, 15),
            user_id=test_user.id
        )

    # Пустая категория
    with pytest.raises(ValueError, match="Transaction category cannot be empty"):
        repo.create(
            name="Покупка",
            type=TransactionType.EXPENSE,
            category="",
            amount=1000.0,
            transaction_date=date(2024, 1, 15),
            user_id=test_user.id
        )

    # Дата в будущем
    future_date = date.today().replace(year=date.today().year + 1)
    with pytest.raises(ValueError, match="Transaction date cannot be in the future"):
        repo.create(
            name="Покупка",
            type=TransactionType.EXPENSE,
            category="Еда",
            amount=1000.0,
            transaction_date=future_date,
            user_id=test_user.id
        )


def test_get_by_id_success(repo, test_user):
    """Тест получения транзакции по ID."""
    created = repo.create(
        name="Покупка",
        type=TransactionType.EXPENSE,
        category="Еда",
        amount=1000.0,
        transaction_date=date(2024, 1, 15),
        user_id=test_user.id
    )

    fetched = repo.get_by_id(created.id, user_id=test_user.id)

    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.name == "Покупка"
    assert fetched.amount == 1000.0


def test_get_by_id_not_found(repo):
    """Тест получения несуществующей транзакции."""
    transaction = repo.get_by_id(99999)
    assert transaction is None


def test_get_by_id_wrong_user(repo, test_user):
    """Тест получения транзакции другого пользователя."""
    # Создаем транзакцию
    created = repo.create(
        name="Покупка",
        type=TransactionType.EXPENSE,
        category="Еда",
        amount=1000.0,
        transaction_date=date(2024, 1, 15),
        user_id=test_user.id
    )

    # Пытаемся получить с другим user_id
    fetched = repo.get_by_id(created.id, user_id=99999)
    assert fetched is None


def test_get_all_success(repo, test_user):
    """Тест получения всех транзакций."""
    repo.create(
        name="Покупка 1",
        type=TransactionType.EXPENSE,
        category="Еда",
        amount=1000.0,
        transaction_date=date(2024, 1, 15),
        user_id=test_user.id
    )
    repo.create(
        name="Покупка 2",
        type=TransactionType.EXPENSE,
        category="Транспорт",
        amount=500.0,
        transaction_date=date(2024, 1, 16),
        user_id=test_user.id
    )

    transactions, total = repo.get_all(user_id=test_user.id)

    assert total == 2
    assert len(transactions) == 2


def test_get_all_with_filters(repo, test_user):
    """Тест получения транзакций с фильтрами."""
    repo.create(
        name="Покупка еды",
        type=TransactionType.EXPENSE,
        category="Еда",
        amount=1000.0,
        transaction_date=date(2024, 1, 15),
        user_id=test_user.id
    )
    repo.create(
        name="Транспорт",
        type=TransactionType.EXPENSE,
        category="Транспорт",
        amount=500.0,
        transaction_date=date(2024, 1, 16),
        user_id=test_user.id
    )

    # Фильтр по категории
    transactions, total = repo.get_all(
        user_id=test_user.id,
        category="Еда"
    )
    assert total == 1
    assert transactions[0].category == "Еда"

    # Фильтр по типу
    transactions, total = repo.get_all(
        user_id=test_user.id,
        transaction_type=TransactionType.EXPENSE
    )
    assert total == 2

    # Фильтр по дате
    transactions, total = repo.get_all(
        user_id=test_user.id,
        start_date=date(2024, 1, 15),
        end_date=date(2024, 1, 15)
    )
    assert total == 1


def test_get_all_with_pagination(repo, test_user):
    """Тест пагинации при получении транзакций."""
    # Создаем несколько транзакций
    for i in range(5):
        repo.create(
            name=f"Покупка {i}",
            type=TransactionType.EXPENSE,
            category="Еда",
            amount=1000.0 + i,
            transaction_date=date(2024, 1, 15 + i),
            user_id=test_user.id
        )

    # Первая страница
    transactions, total = repo.get_all(
        user_id=test_user.id,
        skip=0,
        limit=2
    )
    assert total == 5
    assert len(transactions) == 2

    # Вторая страница
    transactions, total = repo.get_all(
        user_id=test_user.id,
        skip=2,
        limit=2
    )
    assert total == 5
    assert len(transactions) == 2


def test_update_transaction_success(repo, test_user):
    """Тест успешного обновления транзакции."""
    created = repo.create(
        name="Покупка",
        type=TransactionType.EXPENSE,
        category="Еда",
        amount=1000.0,
        transaction_date=date(2024, 1, 15),
        user_id=test_user.id
    )

    updated = repo.update(
        transaction_id=created.id,
        user_id=test_user.id,
        name="Обновленная покупка",
        amount=1500.0
    )

    assert updated is not None
    assert updated.name == "Обновленная покупка"
    assert updated.amount == 1500.0


def test_update_transaction_not_found(repo, test_user):
    """Тест обновления несуществующей транзакции."""
    updated = repo.update(
        transaction_id=99999,
        user_id=test_user.id,
        name="Обновленная покупка"
    )

    assert updated is None


def test_update_transaction_wrong_user(repo, test_user):
    """Тест обновления транзакции другого пользователя."""
    created = repo.create(
        name="Покупка",
        type=TransactionType.EXPENSE,
        category="Еда",
        amount=1000.0,
        transaction_date=date(2024, 1, 15),
        user_id=test_user.id
    )

    updated = repo.update(
        transaction_id=created.id,
        user_id=99999,
        name="Обновленная покупка"
    )

    assert updated is None


def test_update_transaction_validation_errors(repo, test_user):
    """Тест валидации при обновлении транзакции."""
    created = repo.create(
        name="Покупка",
        type=TransactionType.EXPENSE,
        category="Еда",
        amount=1000.0,
        transaction_date=date(2024, 1, 15),
        user_id=test_user.id
    )

    # Пустое имя
    with pytest.raises(ValueError, match="Transaction name cannot be empty"):
        repo.update(
            transaction_id=created.id,
            user_id=test_user.id,
            name=""
        )

    # Отрицательная сумма
    with pytest.raises(ValueError, match="Transaction amount must be positive"):
        repo.update(
            transaction_id=created.id,
            user_id=test_user.id,
            amount=-100.0
        )


def test_delete_transaction_success(repo, test_user):
    """Тест успешного удаления транзакции."""
    created = repo.create(
        name="Покупка",
        type=TransactionType.EXPENSE,
        category="Еда",
        amount=1000.0,
        transaction_date=date(2024, 1, 15),
        user_id=test_user.id
    )

    deleted = repo.delete(created.id, test_user.id)

    assert deleted is True

    # Проверяем, что транзакция удалена
    session = SessionLocal()
    try:
        db_transaction = session.query(Transaction).filter_by(id=created.id).first()
        assert db_transaction is None
    finally:
        session.close()


def test_delete_transaction_not_found(repo, test_user):
    """Тест удаления несуществующей транзакции."""
    deleted = repo.delete(99999, test_user.id)
    assert deleted is False


def test_delete_transaction_wrong_user(repo, test_user):
    """Тест удаления транзакции другого пользователя."""
    created = repo.create(
        name="Покупка",
        type=TransactionType.EXPENSE,
        category="Еда",
        amount=1000.0,
        transaction_date=date(2024, 1, 15),
        user_id=test_user.id
    )

    deleted = repo.delete(created.id, 99999)
    assert deleted is False

