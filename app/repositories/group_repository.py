"""Репозиторий для работы с группами.

TODO: Реализовать методы для работы с группами в БД
"""

# from typing import List, Optional
# from sqlalchemy.orm import Session
# from app.db.models import Group, UserGroup, GroupRole
# from app.repositories.base_repository import BaseRepository


# class GroupRepository(BaseRepository[Group]):
#     """Репозиторий для работы с группами."""
#
#     def __init__(self, db: Session):
#         """Инициализация репозитория.
#
#         Args:
#             db: Сессия базы данных
#         """
#         super().__init__(Group, db)
#
#     def get_by_user_id(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Group]:
#         """Получить группы пользователя.
#
#         Args:
#             user_id: ID пользователя
#             skip: Количество пропущенных записей
#             limit: Максимальное количество записей
#
#         Returns:
#             List[Group]: Список групп
#         """
#         return (
#             self.db.query(Group)
#             .join(UserGroup)
#             .filter(UserGroup.user_id == user_id)
#             .offset(skip)
#             .limit(limit)
#             .all()
#         )
#
#     def get_members(self, group_id: int) -> List[UserGroup]:
#         """Получить участников группы.
#
#         Args:
#             group_id: ID группы
#
#         Returns:
#             List[UserGroup]: Список участников
#         """
#         return (
#             self.db.query(UserGroup)
#             .filter(UserGroup.group_id == group_id)
#             .all()
#         )
#
#     def add_member(self, group_id: int, user_id: int, role: GroupRole = GroupRole.MEMBER) -> UserGroup:
#         """Добавить участника в группу.
#
#         Args:
#             group_id: ID группы
#             user_id: ID пользователя
#             role: Роль участника
#
#         Returns:
#             UserGroup: Связь пользователя и группы
#         """
#         user_group = UserGroup(group_id=group_id, user_id=user_id, role=role)
#         self.db.add(user_group)
#         self.db.commit()
#         self.db.refresh(user_group)
#         return user_group
#
#     def remove_member(self, group_id: int, user_id: int) -> None:
#         """Удалить участника из группы.
#
#         Args:
#             group_id: ID группы
#             user_id: ID пользователя
#         """
#         user_group = (
#             self.db.query(UserGroup)
#             .filter(UserGroup.group_id == group_id, UserGroup.user_id == user_id)
#             .first()
#         )
#         if user_group:
#             self.db.delete(user_group)
#             self.db.commit()

