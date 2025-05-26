from enum import Enum
from typing import Any, ClassVar


class Permissions:
    names: ClassVar[list[str]] = []

    @classmethod
    def get(cls, **kwargs: Any) -> dict[str, bool]:
        return {perm: kwargs.get(perm, False) for perm in cls.names}

    @classmethod
    def get_all(cls) -> dict[str, bool]:
        return cls.get(**dict.fromkeys(cls.names, True))


class TaskPermissions(Permissions):
    names: ClassVar[list[str]] = [
        "request",
        "unrequest",
        "create",
        "update",
        "cancel",
        "delete",
    ]


class SchedulePermissions(Permissions):
    names: ClassVar[list[str]] = ["create", "update", "delete"]


class UserPermissions(Permissions):
    names: ClassVar[list[str]] = [
        "read",
        "create",
        "update",
        "delete",
        "change_password",
        "ssh_keys",
    ]


class ZimPermissions(Permissions):
    names: ClassVar[list[str]] = ["upload"]


class RoleEnum(Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    EDITOR = "editor"
    EDITOR_REQUESTER = "editor-requester"
    WORKER = "worker"
    PROCESSOR = "processor"


ROLES: dict[str, dict[str, Any]] = {
    RoleEnum.ADMIN.value: {
        "tasks": TaskPermissions.get_all(),
        "schedules": SchedulePermissions.get_all(),
        "users": UserPermissions.get_all(),
        "zim": ZimPermissions.get_all(),
    },
    RoleEnum.MANAGER.value: {
        "tasks": TaskPermissions.get(request=True, unrequest=True, cancel=True),
        "schedules": SchedulePermissions.get(create=True, update=True, delete=True),
        "users": UserPermissions.get(
            read=True, create=True, update=True, delete=True, change_password=True
        ),
    },
    RoleEnum.EDITOR.value: {
        "schedules": SchedulePermissions.get(create=True, update=True)
    },
    "editor-requester": {
        "tasks": TaskPermissions.get(request=True, unrequest=True, cancel=True),
        "schedules": SchedulePermissions.get(create=True, update=True),
    },
    RoleEnum.WORKER.value: {
        "tasks": TaskPermissions.get(create=True, update=True, cancel=True),
        "zim": ZimPermissions.get(upload=True),
    },
    RoleEnum.PROCESSOR.value: {"tasks": TaskPermissions.get(update=True)},
}


def get_role_for(permissions: dict[str, bool]) -> str:
    for role_name, role_perms in ROLES.items():
        if role_perms == permissions:
            return role_name
    return "custom"
