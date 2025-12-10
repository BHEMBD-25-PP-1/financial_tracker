"""Репозиторий для работы с группами."""

from contextlib import contextmanager
from typing import List, Optional

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models import Group, User, UserGroup, GroupRole
from app.db.session import SessionLocal
from app.repositories.base_repository import BaseRepository


class GroupRepository(BaseRepository[Group]):
    """Репозиторий для работы с группами."""

    def __init__(self, db_session: Optional[Session] = None):
        """Инициализация репозитория."""
        self.db = db_session or SessionLocal()
        self._owns_session = db_session is None
        self._logger = None
        super().__init__(Group, self.db)

    def __enter__(self):
        """Вход в context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Выход из context manager."""
        if self._owns_session:
            self.db.close()

    @property
    def logger(self):
        """Логгер для репозитория."""
        if self._logger is None:
            import logging
            self._logger = logging.getLogger(__name__)
        return self._logger

    @contextmanager
    def _transaction(self):
        """Context manager для управления транзакциями."""
        try:
            yield self.db
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Transaction failed: {e}")
            raise

    def create(self, name: str, owner_id: int) -> Group:
        """Создать новую группу.

        Args:
            name: Название группы
            owner_id: ID владельца группы

        Returns:
            Group: Созданная группа
        """
        self.logger.info(f"Creating group: name={name}, owner_id={owner_id}")

        if not name or not name.strip():
            raise ValueError("Group name cannot be empty")
        if len(name.strip()) > 200:
            raise ValueError("Group name too long (max 200 characters)")

        try:
            with self._transaction():
                # Проверяем существование пользователя
                user = self.db.query(User).filter(User.id == owner_id).first()
                if not user:
                    raise ValueError(f"User with ID {owner_id} not found")

                group = Group(name=name.strip(), owner_id=owner_id)
                self.db.add(group)
                self.db.flush()

                # Автоматически добавляем владельца в группу
                user_group = UserGroup(
                    group_id=group.id,
                    user_id=owner_id,
                    role=GroupRole.OWNER
                )
                self.db.add(user_group)
                self.db.flush()

                self.logger.info(f"Group created successfully with id: {group.id}")
                return group
        except IntegrityError as e:
            self.logger.error(f"Failed to create group: {e}")
            raise ValueError(f"Database integrity error: {e}") from e
        except SQLAlchemyError as e:
            self.logger.error(f"Database error while creating group: {e}")
            raise RuntimeError(f"Database error: {e}") from e

    def get_by_id(self, group_id: int) -> Optional[Group]:
        """Получить группу по ID."""
        self.logger.debug(f"Fetching group by id: {group_id}")

        try:
            group = self.db.query(Group).filter(Group.id == group_id).first()
            if group:
                self.logger.debug(f"Group found: id={group.id}, name={group.name}")
            else:
                self.logger.debug(f"Group not found: id={group_id}")
            return group
        except SQLAlchemyError as e:
            self.logger.error(f"Database error while fetching group by id {group_id}: {e}")
            raise RuntimeError(f"Database error: {e}") from e

    def get_by_user_id(self, user_id: int, skip: int = 0, limit: int = 100) -> tuple[List[Group], int]:
        """Получить группы пользователя.

        Args:
            user_id: ID пользователя
            skip: Количество пропущенных записей
            limit: Максимальное количество записей

        Returns:
            tuple: (Список групп, общее количество)
        """
        self.logger.debug(f"Fetching groups for user: {user_id}")

        try:
            query = (
                self.db.query(Group)
                .join(UserGroup)
                .filter(UserGroup.user_id == user_id)
            )

            total = query.count()
            groups = query.offset(skip).limit(limit).all()

            self.logger.debug(f"Found {len(groups)} groups (total: {total})")
            return groups, total
        except SQLAlchemyError as e:
            self.logger.error(f"Database error while fetching groups: {e}")
            raise RuntimeError(f"Database error: {e}") from e

    def update(self, group_id: int, owner_id: int, name: Optional[str] = None) -> Optional[Group]:
        """Обновить группу.

        Args:
            group_id: ID группы
            owner_id: ID владельца (для проверки прав)
            name: Новое название группы

        Returns:
            Group: Обновленная группа или None если не найдена или нет прав
        """
        self.logger.info(f"Updating group: id={group_id}, owner_id={owner_id}")

        try:
            with self._transaction():
                group = self.db.query(Group).filter(Group.id == group_id).first()
                if not group:
                    return None

                # Проверяем права владельца
                if group.owner_id != owner_id:
                    self.logger.warning(f"Access denied: user {owner_id} is not owner of group {group_id}")
                    return None

                if name is not None:
                    if not name or not name.strip():
                        raise ValueError("Group name cannot be empty")
                    if len(name.strip()) > 200:
                        raise ValueError("Group name too long (max 200 characters)")
                    group.name = name.strip()

                self.db.flush()
                self.logger.info(f"Group updated successfully: id={group.id}")
                return group
        except ValueError as e:
            self.logger.error(f"Validation error while updating group {group_id}: {e}")
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"Database error while updating group {group_id}: {e}")
            raise RuntimeError(f"Database error: {e}") from e

    def delete(self, group_id: int, owner_id: int) -> bool:
        """Удалить группу.

        Args:
            group_id: ID группы
            owner_id: ID владельца (для проверки прав)

        Returns:
            bool: True если удалено успешно
        """
        self.logger.info(f"Deleting group: id={group_id}, owner_id={owner_id}")

        try:
            with self._transaction():
                group = self.db.query(Group).filter(Group.id == group_id).first()
                if not group:
                    return False

                # Проверяем права владельца
                if group.owner_id != owner_id:
                    self.logger.warning(f"Access denied: user {owner_id} is not owner of group {group_id}")
                    return False

                # Удаляем все связи пользователей с группой
                self.db.query(UserGroup).filter(UserGroup.group_id == group_id).delete()

                # Удаляем группу
                self.db.delete(group)
                self.db.flush()
                self.logger.info(f"Group deleted successfully: id={group_id}")
                return True
        except SQLAlchemyError as e:
            self.logger.error(f"Database error while deleting group {group_id}: {e}")
            raise RuntimeError(f"Database error: {e}") from e

    def get_members(self, group_id: int) -> List[UserGroup]:
        """Получить участников группы.

        Args:
            group_id: ID группы

        Returns:
            List[UserGroup]: Список участников
        """
        self.logger.debug(f"Fetching members for group: {group_id}")

        try:
            members = (
                self.db.query(UserGroup)
                .filter(UserGroup.group_id == group_id)
                .all()
            )
            self.logger.debug(f"Found {len(members)} members")
            return members
        except SQLAlchemyError as e:
            self.logger.error(f"Database error while fetching members: {e}")
            raise RuntimeError(f"Database error: {e}") from e

    def add_member(self, group_id: int, user_id: int, owner_id: int, role: GroupRole = GroupRole.MEMBER) -> UserGroup:
        """Добавить участника в группу.

        Args:
            group_id: ID группы
            user_id: ID пользователя
            owner_id: ID владельца группы (для проверки прав)
            role: Роль участника

        Returns:
            UserGroup: Связь пользователя и группы
        """
        self.logger.info(f"Adding member to group: group_id={group_id}, user_id={user_id}")

        try:
            with self._transaction():
                # Проверяем права владельца
                group = self.db.query(Group).filter(Group.id == group_id).first()
                if not group:
                    raise ValueError(f"Group with ID {group_id} not found")
                if group.owner_id != owner_id:
                    raise ValueError("Only group owner can add members")

                # Проверяем существование пользователя
                user = self.db.query(User).filter(User.id == user_id).first()
                if not user:
                    raise ValueError(f"User with ID {user_id} not found")

                # Проверяем, не является ли пользователь уже участником
                existing = (
                    self.db.query(UserGroup)
                    .filter(UserGroup.group_id == group_id, UserGroup.user_id == user_id)
                    .first()
                )
                if existing:
                    raise ValueError(f"User {user_id} is already a member of group {group_id}")

                user_group = UserGroup(group_id=group_id, user_id=user_id, role=role)
                self.db.add(user_group)
                self.db.flush()
                self.logger.info(f"Member added successfully: group_id={group_id}, user_id={user_id}")
                return user_group
        except IntegrityError as e:
            self.logger.error(f"Failed to add member: {e}")
            raise ValueError(f"Database integrity error: {e}") from e
        except SQLAlchemyError as e:
            self.logger.error(f"Database error while adding member: {e}")
            raise RuntimeError(f"Database error: {e}") from e

    def remove_member(self, group_id: int, user_id: int, requester_id: int) -> bool:
        """Удалить участника из группы.

        Args:
            group_id: ID группы
            user_id: ID пользователя для удаления
            requester_id: ID пользователя, который запрашивает удаление

        Returns:
            bool: True если удалено успешно
        """
        self.logger.info(f"Removing member from group: group_id={group_id}, user_id={user_id}")

        try:
            with self._transaction():
                group = self.db.query(Group).filter(Group.id == group_id).first()
                if not group:
                    return False

                # Проверяем права: владелец может удалить любого, участник может удалить себя
                if group.owner_id != requester_id and user_id != requester_id:
                    raise ValueError("Only group owner can remove other members")

                user_group = (
                    self.db.query(UserGroup)
                    .filter(UserGroup.group_id == group_id, UserGroup.user_id == user_id)
                    .first()
                )
                if not user_group:
                    return False

                # Нельзя удалить владельца группы
                if user_group.role == GroupRole.OWNER:
                    raise ValueError("Cannot remove group owner")

                self.db.delete(user_group)
                self.db.flush()
                self.logger.info(f"Member removed successfully: group_id={group_id}, user_id={user_id}")
                return True
        except ValueError as e:
            self.logger.error(f"Validation error while removing member: {e}")
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"Database error while removing member: {e}")
            raise RuntimeError(f"Database error: {e}") from e

    def is_member(self, group_id: int, user_id: int) -> bool:
        """Проверить, является ли пользователь участником группы.

        Args:
            group_id: ID группы
            user_id: ID пользователя

        Returns:
            bool: True если пользователь является участником
        """
        user_group = (
            self.db.query(UserGroup)
            .filter(UserGroup.group_id == group_id, UserGroup.user_id == user_id)
            .first()
        )
        return user_group is not None

    def close(self):
        """Закрыть сессию базы данных."""
        if self._owns_session:
            self.db.close()
            self.logger.debug("Database session closed")
