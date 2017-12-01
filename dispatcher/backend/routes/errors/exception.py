from flask import Response, jsonify




class UsernameNotValid(Exception):
    pass

class ScopeNotValid(Exception):
    pass

# 401 Unauthorized





# 404 Not Found
class UserDoesNotExist(Exception):
    pass

class TaskDoesNotExist(Exception):
    pass

# 409 Conflict
class UserAlreadyExists(Exception):
    pass

