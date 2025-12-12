"""Тесты для GroupRepository."""

import sys
from pathlib import Path

import pytest
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

# Ensure project modules are importable when running pytest from repo root
PROJECT_ROOT = Path(__file__).resolve().parents[0]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db.base import Base
from app.db.models import Group, User, UserGroup, GroupRole
from app.repositories.group_repository import GroupRepository
from app.db import session as db_session


@pytest.fixture(autouse=True)
def clean_groups_table():
    """Очистка таблиц перед и после каждого теста."""
    session = db_session.SessionLocal()
    try:
        session.query(UserGroup).delete()
        session.query(Group).delete()
        session.query(User).delete()
        session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()
    yield
    session = db_session.SessionLocal()
    try:
        session.query(UserGroup).delete()
        session.query(Group).delete()
        session.query(User).delete()
        session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()


@pytest.fixture
def test_user():
    """Создание тестового пользователя."""
    from app.repositories.user_repository import UserRepository
    
    session = db_session.SessionLocal()
    try:
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
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@pytest.fixture
def test_user2():
    """Создание второго тестового пользователя."""
    from app.repositories.user_repository import UserRepository
    
    session = db_session.SessionLocal()
    try:
        existing_user = session.query(User).filter(User.login == "test_user2").first()
        if existing_user:
            yield existing_user
        else:
            user_repo = UserRepository(db_session=session)
            user = user_repo.add(
                first_name="Test2",
                last_name="User2",
                login="test_user2",
                password="testpassword123"
            )
            session.commit()
            session.refresh(user)
            yield user
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@pytest.fixture
def repo():
    """Фикстура для создания репозитория."""
    with GroupRepository() as repository:
        yield repository


def test_create_group_success(repo, test_user):
    """Тест создания группы и сохранения в БД."""
    group = repo.create(name="Test Group", owner_id=test_user.id)

    assert group.id is not None
    assert group.name == "Test Group"
    assert group.owner_id == test_user.id

    session = db_session.SessionLocal()
    try:
        db_group = session.query(Group).filter_by(id=group.id).one()
        assert db_group.name == "Test Group"
        
        user_group = session.query(UserGroup).filter_by(
            group_id=group.id,
            user_id=test_user.id
        ).first()
        assert user_group is not None
        assert user_group.role == GroupRole.OWNER
    finally:
        session.close()


def test_create_group_empty_name(repo, test_user):
    """Тест создания группы с пустым именем."""
    with pytest.raises(ValueError, match="Group name cannot be empty"):
        repo.create(name="", owner_id=test_user.id)


def test_create_group_whitespace_name(repo, test_user):
    """Тест создания группы с именем из пробелов."""
    with pytest.raises(ValueError, match="Group name cannot be empty"):
        repo.create(name="   ", owner_id=test_user.id)


def test_create_group_long_name(repo, test_user):
    """Тест создания группы с слишком длинным именем."""
    long_name = "A" * 201
    with pytest.raises(ValueError, match="Group name too long"):
        repo.create(name=long_name, owner_id=test_user.id)


def test_create_group_invalid_user(repo):
    """Тест создания группы с несуществующим пользователем."""
    with pytest.raises(ValueError, match="User with ID.*not found"):
        repo.create(name="Test Group", owner_id=99999)


def test_get_by_id_success(repo, test_user):
    """Тест получения группы по ID."""
    created = repo.create(name="Test Group", owner_id=test_user.id)

    fetched = repo.get_by_id(created.id)

    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.name == "Test Group"


def test_get_by_id_not_found(repo):
    """Тест получения несуществующей группы."""
    group = repo.get_by_id(99999)
    assert group is None


def test_get_by_user_id_success(repo, test_user):
    """Тест получения групп пользователя."""
    group1 = repo.create(name="Group 1", owner_id=test_user.id)
    group2 = repo.create(name="Group 2", owner_id=test_user.id)

    groups, total = repo.get_by_user_id(test_user.id)

    assert total == 2
    assert len(groups) == 2
    group_ids = [g.id for g in groups]
    assert group1.id in group_ids
    assert group2.id in group_ids


def test_get_by_user_id_with_pagination(repo, test_user):
    """Тест пагинации при получении групп."""
    for i in range(5):
        repo.create(name=f"Group {i}", owner_id=test_user.id)

    # Первая страница
    groups, total = repo.get_by_user_id(test_user.id, skip=0, limit=2)
    assert total == 5
    assert len(groups) == 2

    # Вторая страница
    groups, total = repo.get_by_user_id(test_user.id, skip=2, limit=2)
    assert total == 5
    assert len(groups) == 2


def test_update_group_success(repo, test_user):
    """Тест успешного обновления группы."""
    created = repo.create(name="Test Group", owner_id=test_user.id)

    updated = repo.update(created.id, test_user.id, name="Updated Group")

    assert updated is not None
    assert updated.name == "Updated Group"
    assert updated.id == created.id


def test_update_group_not_found(repo, test_user):
    """Тест обновления несуществующей группы."""
    updated = repo.update(99999, test_user.id, name="Updated Group")
    assert updated is None


def test_update_group_wrong_owner(repo, test_user, test_user2):
    """Тест обновления группы другим пользователем."""
    created = repo.create(name="Test Group", owner_id=test_user.id)

    updated = repo.update(created.id, test_user2.id, name="Updated Group")
    assert updated is None


def test_update_group_empty_name(repo, test_user):
    """Тест обновления группы с пустым именем."""
    created = repo.create(name="Test Group", owner_id=test_user.id)

    with pytest.raises(ValueError, match="Group name cannot be empty"):
        repo.update(created.id, test_user.id, name="")


def test_update_group_long_name(repo, test_user):
    """Тест обновления группы с слишком длинным именем."""
    created = repo.create(name="Test Group", owner_id=test_user.id)
    long_name = "A" * 201

    with pytest.raises(ValueError, match="Group name too long"):
        repo.update(created.id, test_user.id, name=long_name)


def test_delete_group_success(repo, test_user):
    """Тест успешного удаления группы."""
    created = repo.create(name="Test Group", owner_id=test_user.id)

    deleted = repo.delete(created.id, test_user.id)

    assert deleted is True

    session = db_session.SessionLocal()
    try:
        db_group = session.query(Group).filter_by(id=created.id).first()
        assert db_group is None
    finally:
        session.close()


def test_delete_group_not_found(repo, test_user):
    """Тест удаления несуществующей группы."""
    deleted = repo.delete(99999, test_user.id)
    assert deleted is False


def test_delete_group_wrong_owner(repo, test_user, test_user2):
    """Тест удаления группы другим пользователем."""
    created = repo.create(name="Test Group", owner_id=test_user.id)

    deleted = repo.delete(created.id, test_user2.id)
    assert deleted is False


def test_get_members_success(repo, test_user, test_user2):
    """Тест получения участников группы."""
    group = repo.create(name="Test Group", owner_id=test_user.id)
    
    repo.add_member(group.id, test_user2.id, test_user.id, GroupRole.MEMBER)

    members = repo.get_members(group.id)

    assert len(members) == 2
    user_ids = [m.user_id for m in members]
    assert test_user.id in user_ids
    assert test_user2.id in user_ids


def test_get_members_empty_group(repo, test_user):
    """Тест получения участников пустой группы."""
    group = repo.create(name="Test Group", owner_id=test_user.id)
    
    session = db_session.SessionLocal()
    try:
        session.query(UserGroup).filter_by(group_id=group.id).delete()
        session.commit()
    finally:
        session.close()

    members = repo.get_members(group.id)
    assert len(members) == 0


def test_add_member_success(repo, test_user, test_user2):
    """Тест успешного добавления участника."""
    group = repo.create(name="Test Group", owner_id=test_user.id)

    user_group = repo.add_member(group.id, test_user2.id, test_user.id, GroupRole.MEMBER)

    assert user_group is not None
    assert user_group.group_id == group.id
    assert user_group.user_id == test_user2.id
    assert user_group.role == GroupRole.MEMBER


def test_add_member_group_not_found(repo, test_user, test_user2):
    """Тест добавления участника в несуществующую группу."""
    with pytest.raises(ValueError, match="Group with ID.*not found"):
        repo.add_member(99999, test_user2.id, test_user.id, GroupRole.MEMBER)


def test_add_member_user_not_found(repo, test_user):
    """Тест добавления несуществующего пользователя."""
    group = repo.create(name="Test Group", owner_id=test_user.id)

    with pytest.raises(ValueError, match="User with ID.*not found"):
        repo.add_member(group.id, 99999, test_user.id, GroupRole.MEMBER)


def test_add_member_not_owner(repo, test_user, test_user2):
    """Тест добавления участника не владельцем."""
    group = repo.create(name="Test Group", owner_id=test_user.id)

    with pytest.raises(ValueError, match="Only group owner can add members"):
        repo.add_member(group.id, test_user2.id, test_user2.id, GroupRole.MEMBER)


def test_add_member_duplicate(repo, test_user, test_user2):
    """Тест добавления уже существующего участника."""
    group = repo.create(name="Test Group", owner_id=test_user.id)
    repo.add_member(group.id, test_user2.id, test_user.id, GroupRole.MEMBER)

    with pytest.raises(ValueError, match="already a member"):
        repo.add_member(group.id, test_user2.id, test_user.id, GroupRole.MEMBER)


def test_remove_member_success(repo, test_user, test_user2):
    """Тест успешного удаления участника."""
    group = repo.create(name="Test Group", owner_id=test_user.id)
    repo.add_member(group.id, test_user2.id, test_user.id, GroupRole.MEMBER)

    removed = repo.remove_member(group.id, test_user2.id, test_user.id)

    assert removed is True

    session = db_session.SessionLocal()
    try:
        user_group = session.query(UserGroup).filter_by(
            group_id=group.id,
            user_id=test_user2.id
        ).first()
        assert user_group is None
    finally:
        session.close()


def test_remove_member_self(repo, test_user, test_user2):
    """Тест удаления участником самого себя."""
    group = repo.create(name="Test Group", owner_id=test_user.id)
    repo.add_member(group.id, test_user2.id, test_user.id, GroupRole.MEMBER)

    removed = repo.remove_member(group.id, test_user2.id, test_user2.id)

    assert removed is True


def test_remove_member_group_not_found(repo, test_user, test_user2):
    """Тест удаления участника из несуществующей группы."""
    removed = repo.remove_member(99999, test_user2.id, test_user.id)
    assert removed is False


def test_remove_member_not_member(repo, test_user, test_user2):
    """Тест удаления несуществующего участника."""
    group = repo.create(name="Test Group", owner_id=test_user.id)

    removed = repo.remove_member(group.id, test_user2.id, test_user.id)
    assert removed is False


def test_remove_member_not_owner_or_self(repo, test_user, test_user2):
    """Тест удаления участника не владельцем и не самим собой."""
    group = repo.create(name="Test Group", owner_id=test_user.id)
    repo.add_member(group.id, test_user2.id, test_user.id, GroupRole.MEMBER)

    from app.repositories.user_repository import UserRepository
    session = db_session.SessionLocal()
    try:
        user_repo = UserRepository(db_session=session)
        user3 = user_repo.add(
            first_name="Test3",
            last_name="User3",
            login="test_user3",
            password="testpassword123"
        )
        session.commit()
        session.refresh(user3)

        with pytest.raises(ValueError, match="Only group owner can remove other members"):
            repo.remove_member(group.id, test_user2.id, user3.id)
    finally:
        session.close()


def test_remove_member_owner(repo, test_user):
    """Тест попытки удаления владельца группы."""
    group = repo.create(name="Test Group", owner_id=test_user.id)

    with pytest.raises(ValueError, match="Cannot remove group owner"):
        repo.remove_member(group.id, test_user.id, test_user.id)


def test_is_member_true(repo, test_user, test_user2):
    """Тест проверки участника - пользователь является участником."""
    group = repo.create(name="Test Group", owner_id=test_user.id)
    repo.add_member(group.id, test_user2.id, test_user.id, GroupRole.MEMBER)

    assert repo.is_member(group.id, test_user.id) is True
    assert repo.is_member(group.id, test_user2.id) is True


def test_is_member_false(repo, test_user, test_user2):
    """Тест проверки участника - пользователь не является участником."""
    group = repo.create(name="Test Group", owner_id=test_user.id)

    assert repo.is_member(group.id, test_user2.id) is False


def test_is_member_group_not_found(repo, test_user):
    """Тест проверки участника для несуществующей группы."""
    assert repo.is_member(99999, test_user.id) is False
