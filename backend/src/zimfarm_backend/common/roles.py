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


class ResourcePermissions(Permissions):
    names: ClassVar[list[str]] = ["create", "read", "update", "delete"]


class TaskPermissions(Permissions):
    names: ClassVar[list[str]] = [*ResourcePermissions.names, "secrets", "cancel"]


class RecipePermissions(Permissions):
    names: ClassVar[list[str]] = [*ResourcePermissions.names, "secrets", "archive"]


class RequestedTaskPermissions(Permissions):
    names: ClassVar[list[str]] = [*ResourcePermissions.names, "secrets"]


class AccountPermissions(Permissions):
    names: ClassVar[list[str]] = [
        *ResourcePermissions.names,
        "change_password",
        "secrets",
    ]


class WorkerPermissions(Permissions):
    names: ClassVar[list[str]] = [
        "read",
        "update",
        "create",
        "secrets",
        "ssh_keys",
        "checkin",
    ]


class ZimPermissions(Permissions):
    names: ClassVar[list[str]] = ["upload"]


class OfflinerPermissions(Permissions):
    names: ClassVar[list[str]] = ["read", "create", "update"]


class RoleEnum(StrEnum):
    ADMIN = "admin"
    MANAGER = "manager"
    GLOBAL_EDITOR = "global-editor"
    TEAM_EDITOR = "team-editor"
    GLOBAL_EDITOR_REQUESTER = "global-editor-requester"
    TEAM_EDITOR_REQUESTER = "team-editor-requester"
    WORKER = "worker"
    PROCESSOR = "processor"
    TEAM_VIEWER = "team-viewer"
    PUBLIC_VIEWER = "public-viewer"
    GLOBAL_VIEWER = "global-viewer"


GLOBAL_ROLES: frozenset[RoleEnum] = frozenset(
    {
        RoleEnum.ADMIN,
        RoleEnum.MANAGER,
        RoleEnum.GLOBAL_EDITOR,
        RoleEnum.GLOBAL_EDITOR_REQUESTER,
        RoleEnum.GLOBAL_VIEWER,
        RoleEnum.WORKER,
        RoleEnum.PROCESSOR,
    }
)

TEAM_ROLES: frozenset[RoleEnum] = frozenset(
    {
        RoleEnum.TEAM_EDITOR,
        RoleEnum.TEAM_EDITOR_REQUESTER,
        RoleEnum.TEAM_VIEWER,
    }
)


def is_global_role(role: RoleEnum) -> bool:
    """Whether the role has access to all teams (i.e. is not team-scoped)."""
    return role in GLOBAL_ROLES


def is_team_role(role: RoleEnum) -> bool:
    """Whether the role is scoped to the teams it is a member of."""
    return role in TEAM_ROLES


ROLES: dict[str, dict[str, dict[str, bool]]] = {
    RoleEnum.ADMIN: {
        "tasks": TaskPermissions.get_all(),
        "recipes": RecipePermissions.get_all(),
        "accounts": AccountPermissions.get_all(),
        "zim": ZimPermissions.get_all(),
        "workers": WorkerPermissions.get_all(),
        "requested_tasks": RequestedTaskPermissions.get_all(),
        "offliners": OfflinerPermissions.get_all(),
        "teams": ResourcePermissions.get_all(),
    },
    RoleEnum.MANAGER: {
        "tasks": TaskPermissions.get(read=True, cancel=True, secrets=True),
        "recipes": RecipePermissions.get(
            read=True,
            create=True,
            update=True,
            archive=True,
            secrets=True,
        ),
        "accounts": AccountPermissions.get(
            read=True,
            create=True,
            update=True,
            delete=True,
            change_password=True,
            secrets=True,
        ),
        "workers": WorkerPermissions.get(read=True, ssh_keys=True),
        "requested_tasks": RequestedTaskPermissions.get(
            read=True, create=True, delete=True, secrets=True
        ),
        "teams": ResourcePermissions.get(read=True),
    },
    RoleEnum.GLOBAL_EDITOR: {
        "recipes": RecipePermissions.get(
            read=True, create=True, update=True, secrets=True, archive=True
        ),
    },
    RoleEnum.TEAM_EDITOR: {
        "recipes": RecipePermissions.get(
            read=True, create=True, update=True, secrets=True, archive=True
        ),
    },
    RoleEnum.GLOBAL_EDITOR_REQUESTER.value: {
        "tasks": TaskPermissions.get(read=True, cancel=True, secrets=True),
        "recipes": RecipePermissions.get(
            read=True, create=True, update=True, secrets=True, archive=True
        ),
        "requested_tasks": RequestedTaskPermissions.get(
            read=True, create=True, delete=True, secrets=True
        ),
    },
    RoleEnum.TEAM_EDITOR_REQUESTER.value: {
        "tasks": TaskPermissions.get(read=True, cancel=True, secrets=True),
        "recipes": RecipePermissions.get(
            read=True, create=True, update=True, secrets=True, archive=True
        ),
        "requested_tasks": RequestedTaskPermissions.get(
            read=True, create=True, delete=True, secrets=True
        ),
    },
    RoleEnum.WORKER: {
        "tasks": TaskPermissions.get(
            read=True, create=True, update=True, cancel=True, secrets=True
        ),
        "requested_tasks": RequestedTaskPermissions.get(
            read=True, create=True, delete=True, secrets=True, update=True
        ),
        "workers": WorkerPermissions.get(read=True, checkin=True),
        "zim": ZimPermissions.get(upload=True),
    },
    RoleEnum.PROCESSOR: {
        "tasks": TaskPermissions.get(update=True, secrets=True),
        "requested_tasks": RequestedTaskPermissions.get(update=True, secrets=True),
    },
    RoleEnum.PUBLIC_VIEWER: {},
    RoleEnum.GLOBAL_VIEWER.value: {
        "tasks": TaskPermissions.get(read=True),
        "recipes": RecipePermissions.get(read=True),
        "requested_tasks": RequestedTaskPermissions.get(read=True),
    },
}


def merge_scopes(
    user_scope: dict[str, dict[str, bool]], all_scopes: dict[str, dict[str, bool]]
) -> dict[str, dict[str, bool]]:
    """Combine account scope and all scopes populating missing scopes with False."""
    merged: dict[str, dict[str, bool]] = {}

    for category, permissions in all_scopes.items():
        merged[category] = {}
        user_permissions = user_scope.get(category, {})

        for perm, _ in permissions.items():
            merged[category][perm] = user_permissions.get(perm, False)

    return merged
