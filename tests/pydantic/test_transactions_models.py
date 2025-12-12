import datetime

import pytest
from pydantic import ValidationError

from app.transactions import models as m


def test_transaction_valid_example():
    data = {
        "id": 1,
        "name": "Покупка",
        "type": "EXPENSE",
        "category": "Еда",
        "amount": 100.5,
        "date": datetime.date(2024, 1, 1),
        "user_id": 1,
        "group_id": None,
        "created_at": datetime.datetime(2024, 1, 1, 0, 0),
        "updated_at": datetime.datetime(2024, 1, 1, 0, 0),
    }
    obj = m.Transaction(**data)
    assert obj.type == m.TransactionType.EXPENSE


def test_create_transaction_request_invalid_enum():
    bad = {
        "name": "X",
        "type": "other",
        "category": "Еда",
        "amount": 10,
        "date": datetime.date.today(),
    }
    with pytest.raises(ValidationError):
        m.CreateTransactionRequest(**bad)


def test_update_transaction_request_allows_optional():
    obj = m.UpdateTransactionRequest()
    # Pydantic сохраняет поля со значением None; убедимся, что без значений ошибки нет
    assert obj.model_dump(exclude_none=True) == {}


def test_transaction_list_response_types():
    tx = m.Transaction(
        id=1,
        name="A",
        type="INCOME",
        category="Категория",
        amount=1.0,
        date=datetime.date.today(),
        user_id=1,
        group_id=None,
        created_at=datetime.datetime.utcnow(),
        updated_at=datetime.datetime.utcnow(),
    )
    resp = m.TransactionListResponse(items=[tx], total=1, page=1, size=10)
    assert resp.items[0].id == 1

