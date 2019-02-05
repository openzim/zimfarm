import os

from pymongo import MongoClient
from pymongo.database import Database as BaseDatabase
from pymongo.collection import Collection as BaseCollection


class Client(MongoClient):
    def __init__(self):
        super().__init__(host=os.getenv('MONGO_HOSTNAME', 'mongo'))


class Database(BaseDatabase):
    def __init__(self):
        super().__init__(Client(), 'Zimfarm')


class Users(BaseCollection):
    def __init__(self):
        super().__init__(Database(), 'users')

    def initialize(self):
        self.create_index('username', name='username', unique=True)
        self.create_index('email', name='email', unique=True)
        self.create_index('ssh_keys.fingerprint', name='ssh_keys.fingerprint',
                          partialFilterExpression={'ssh_keys': {'$exists': True}})

        schema = {
            "bsonType": "object",
            "required": ["username", "password_hash"],
            "properties": {
                "username": {"bsonType": "string"},
                "password_hash": {"bsonType": "string"},
                "email": {"bsonType": "string"},
                "ssh_keys": {
                    "bsonType": "array",
                    "items": {
                        "bsonType": "object",
                        "required": ["name", "fingerprint", "key", "type", "added", "last_used"],
                        "properties": {
                            "name": {"bsonType": "string"},
                            "fingerprint": {"bsonType": "string"},
                            "key": {"bsonType": "string"},
                            "type": {"enum": ["RSA"]},
                            "added": {"bsonType": "date"},
                            "last_used": {"bsonType": "date"},
                        },
                        "additionalProperties": False
                    }
                }
            }
        }
        self.database.command({'collMod': 'users', 'validator': {'$jsonSchema': schema}})


class RefreshTokens(BaseCollection):
    def __init__(self):
        super().__init__(Database(), 'refresh_tokens')


class Tasks(BaseCollection):
    def __init__(self):
        super().__init__(Database(), 'tasks')


class Schedules(BaseCollection):
    def __init__(self):
        super().__init__(Database(), 'schedules')


class Workers(BaseCollection):
    def __init__(self):
        super().__init__(Database(), 'workers')
