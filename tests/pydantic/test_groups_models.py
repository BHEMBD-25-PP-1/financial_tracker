import datetime

import pytest
from pydantic import ValidationError

from app.groups import models as m


def test_group_valid():
    data = {
        "id": 1,
        "name": "Семья",
        "owner_id": 1,
        "created_at": datetime.datetime.utcnow(),
        "updated_at": datetime.datetime.utcnow(),
    }
    obj = m.Group(**data)
    assert obj.owner_id == 1


def test_create_group_request_invalid_empty_name():
    with pytest.raises(ValidationError):
        m.CreateGroupRequest(name="")


def test_group_member_role_enum():
    member = m.GroupMember(
        id=1,
        user_id=1,
        group_id=1,
        role="owner",
        joined_at=datetime.datetime.utcnow(),
    )
    assert member.role == m.GroupRole.owner


def test_group_member_invalid_role():
    with pytest.raises(ValidationError):
        m.GroupMember(
            id=1,
            user_id=1,
            group_id=1,
            role="wrong",
            joined_at=datetime.datetime.utcnow(),
        )


def test_group_list_response_items_type():
    g = m.Group(
        id=1,
        name="Семья",
        owner_id=1,
        created_at=datetime.datetime.utcnow(),
        updated_at=datetime.datetime.utcnow(),
    )
    resp = m.GroupListResponse(items=[g], total=1, page=1, size=10)
    assert resp.items[0].name == "Семья"

