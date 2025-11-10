"""Groups API модуль."""

from app.groups.controllers import router
from app.groups.models import (
    AddMemberRequest,
    CreateGroupRequest,
    Error,
    Group,
    GroupAnalyticsResponse,
    GroupListResponse,
    GroupMember,
    GroupMembersResponse,
    GroupRole,
    UpdateGroupRequest,
)

__all__ = [
    "router",
    "Group",
    "GroupRole",
    "CreateGroupRequest",
    "UpdateGroupRequest",
    "GroupListResponse",
    "GroupMember",
    "GroupMembersResponse",
    "AddMemberRequest",
    "GroupAnalyticsResponse",
    "Error",
]

