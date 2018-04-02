from pymongo import MongoClient
from pymongo.database import Database as BaseDatabase
from pymongo.collection import Collection as BaseCollection


class Client(MongoClient):
    def __init__(self):
        super().__init__(host='mongo')


class Database(BaseDatabase):
    def __init__(self):
        super().__init__(Client(), 'Zimfarm')


class Users(BaseCollection):
    username = 'username'
    email = 'email'
    password_hash = 'password_hash'
    scope = 'scope'

    schema = {
        username: {
            'type': 'string',
            'regex': '^[a-zA-Z0-9_.+-]+$',
            'required': True
        },
        email: {
            'type': 'string',
            'regex': '^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        },
        password_hash: {
            'type': 'string',
            'required': True
        },
        scope: {
            'type': 'dict',
            'required': True,
            'keyschema': {'type': 'string'},
            'valueschema': {
                'type': 'dict',
                'keyschema': {'type': 'string'},
                'valueschema': {'type': 'boolean'},
            }
        }
    }

    def __init__(self):
        super().__init__(Database(), 'users')


class RefreshTokens(BaseCollection):
    def __init__(self):
        super().__init__(Database(), 'refreshtokens')


class Tasks(BaseCollection):
    def __init__(self):
        super().__init__(Database(), 'tasks')

    schema = {
        'status': {
            'type': 'string',
            'minlength': 1,
            'maxlength': 25,
            'required': True
        },
        'termination_time': {
            'type': 'datetime',
            'required': True,
            'nullable': True,
        },
        'offliner': {
            'type': 'dict',
            'schema': {
                'name': {
                    'type': 'string',
                    'minlength': 1,
                    'maxlength': 50,
                    'required': True
                },
                'config': {
                    'type': 'dict',
                }
            }
        },
        'logs': {
            'type': 'list'
        }
    }
