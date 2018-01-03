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
    def __init__(self):
        super().__init__(Database(), 'users')

    schema = {
        'username': {
            'type': 'string',
            'minlength': 1,
            'maxlength': 75,
            'required': True
        },
        'password_hash': {
            'type': 'string',
            'required': True
        },
        'is_admin': {
            'type': 'boolean',
            'required': True
        }
    }


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
        'created': {
            'type': 'datetime',
            'required': True
        },
        'started': {
            'type': 'datetime',
            'nullable': True,
            'required': True
        },
        'finished': {
            'type': 'datetime',
            'nullable': True,
            'required': True
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
        'steps': {
            'type': 'list'
        }
    }
