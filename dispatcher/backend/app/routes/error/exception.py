# 400 Bad Request
class InvalidRequest(Exception):
    pass

class UsernameNotValid(Exception):
    pass

class ScopeNotValid(Exception):
    pass

# 401 Unauthorized
class NotEnoughPrivilege(Exception):
    pass

# 401 Unauthorized
class AuthFailed(Exception):
    pass

# 404 Not Found
class UserDoesNotExist(Exception):
    pass

# 409 Conflict
class UserAlreadyExists(Exception):
    pass

# 500 Internal Server Error
class RabbitMQError(Exception):
    def __init__(self, code):
        self.code = code

class RabbitMQPutUserFailed(RabbitMQError):
    pass

class RabbitMQPutPermissionFailed(RabbitMQError):
    pass

class RabbitMQDeleteUserFailed(RabbitMQError):
    pass