from enum import StrEnum
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
        "read",
        "secrets",
        "request",
        "unrequest",
        "create",
        "update",
        "cancel",
        "delete",
    ]


class SchedulePermissions(Permissions):
    names: ClassVar[list[str]] = [
        "read",
        "secrets",
        "create",
        "update",
        "archive",
        "delete",
    ]


class RequestedTaskPermissions(Permissions):
    names: ClassVar[list[str]] = [
        "read",
        "secrets",
        "create",
        "update",
        "delete",
    ]


class UserPermissions(Permissions):
    names: ClassVar[list[str]] = [
        "read",
        "create",
        "update",
        "delete",
        "change_password",
        "ssh_keys",
        "secrets",
    ]


class WorkerPermissions(Permissions):
    names: ClassVar[list[str]] = [
        "read",
        "update",
        "create",
        "secrets",
    ]


class ZimPermissions(Permissions):
    names: ClassVar[list[str]] = ["upload"]


class RoleEnum(StrEnum):
    ADMIN = "admin"
    MANAGER = "manager"
    EDITOR = "editor"
    EDITOR_REQUESTER = "editor-requester"
    WORKER = "worker"
    PROCESSOR = "processor"


ROLES: dict[str, dict[str, Any]] = {
    RoleEnum.ADMIN: {
        "tasks": TaskPermissions.get_all(),
        "schedules": SchedulePermissions.get_all(),
        "users": UserPermissions.get_all(),
        "zim": ZimPermissions.get_all(),
        "workers": WorkerPermissions.get_all(),
        "requested_tasks": RequestedTaskPermissions.get_all(),
    },
    RoleEnum.MANAGER: {
        "tasks": TaskPermissions.get(cancel=True, secrets=True),
        "schedules": SchedulePermissions.get(
            create=True, update=True, validate=True, archive=True, secrets=True
        ),
        "users": UserPermissions.get(
            read=True,
            create=True,
            update=True,
            delete=True,
            change_password=True,
            ssh_keys=True,
            secrets=True,
        ),
        "workers": WorkerPermissions.get(read=True),
    },
    RoleEnum.EDITOR: {
        "schedules": SchedulePermissions.get(create=True, update=True, secrets=True),
    },
    RoleEnum.EDITOR_REQUESTER.value: {
        "tasks": TaskPermissions.get(request=True, unrequest=True, cancel=True),
        "schedules": SchedulePermissions.get(create=True, update=True),
        "requested_tasks": RequestedTaskPermissions.get(create=True, delete=True),
    },
    RoleEnum.WORKER: {
        "tasks": TaskPermissions.get(
            create=True, update=True, cancel=True, secrets=True
        ),
        "requested_tasks": RequestedTaskPermissions.get(
            create=True, delete=True, secrets=True, update=True
        ),
        "workers": WorkerPermissions.get(checkin=True),
        "zim": ZimPermissions.get(upload=True),
    },
    RoleEnum.PROCESSOR: {
        "tasks": TaskPermissions.get(update=True, secrets=True),
        "requested_tasks": RequestedTaskPermissions.get(update=True, secrets=True),
    },
}


def get_role_for(permissions: dict[str, Any]) -> str:
    for role_name, role_perms in ROLES.items():
        if role_perms == permissions:
            return role_name
    return "custom"
