class Permissions:
    names = []

    @classmethod
    def get(cls, **kwargs):
        return {perm: kwargs.get(perm, False) for perm in cls.names}

    @classmethod
    def get_all(cls):
        return cls.get(**{perm: True for perm in cls.names})


class TaskPermissions(Permissions):
    names = ["request", "unrequest", "create", "update", "cancel", "delete"]


class SchedulePermissions(Permissions):
    names = ["create", "update", "delete"]


class UserPermissions(Permissions):
    names = ["read", "create", "update", "delete", "change_password", "ssh_keys"]


class ZimPermissions(Permissions):
    names = ["upload"]


ROLES = {
    "admin": {
        "tasks": TaskPermissions.get_all(),
        "schedules": SchedulePermissions.get_all(),
        "users": UserPermissions.get_all(),
        "zim": ZimPermissions.get_all(),
    },
    "manager": {
        "tasks": TaskPermissions.get(request=True, unrequest=True, cancel=True),
        "schedules": SchedulePermissions.get(create=True, update=True, delete=True),
        "users": UserPermissions.get(
            read=True, create=True, update=True, delete=True, change_password=True
        ),
    },
    "editor": {"schedules": SchedulePermissions.get(create=True, update=True)},
    "worker": {
        "tasks": TaskPermissions.get(create=True, update=True, cancel=True),
        "zim": ZimPermissions.get(upload=True),
    },
    "processor": {"tasks": TaskPermissions.get(update=True)},
}


def get_role_for(permissions):
    for role_name, role_perms in ROLES.items():
        if role_perms == permissions:
            return role_name
    return "custom"
