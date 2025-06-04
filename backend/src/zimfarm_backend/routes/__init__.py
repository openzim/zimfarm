from zimfarm_backend.db.models import User


def check_user_permission(
    user: User,
    *,
    namespace: str,
    name: str,
) -> bool:
    """Check if a user has a permission for a given namespace and name"""
    if user.scope is None:
        return False
    return user.scope.get(namespace, {}).get(name, False)
