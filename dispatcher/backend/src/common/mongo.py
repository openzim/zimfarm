import os

from pymongo import MongoClient
from pymongo.database import Database as BaseDatabase
from pymongo.collection import Collection as BaseCollection
from common.entities import TaskStatus


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
        self.create_index('email', name='email')
        self.create_index('ssh_keys.fingerprint', name='ssh_keys.fingerprint',
                          partialFilterExpression={'ssh_keys': {'$exists': True}})


class RefreshTokens(BaseCollection):
    def __init__(self):
        super().__init__(Database(), 'refresh_tokens')


class Tasks(BaseCollection):
    _name = 'tasks'
    schema = {
        'bsonType': 'object',
        'required': ['status', 'command', 'schedule', 'worker', 'timestamp'],
        'properties': {
            'status': {'enum': TaskStatus.all()},
            'command': {'bsonType': ['string', 'null']},
            'schedule': {'oneOf': [
                {'bsonType': 'null'},
                {
                    'bsonType': 'object',
                    'required': ['_id', 'name'],
                    'properties': {
                        '_id': {'bsonType': 'objectId'},
                        'name': {'bsonType': 'string'},
                    }
                }
            ]},
            'worker': {'oneOf': [
                {'bsonType': 'null'},
                {
                    'bsonType': 'object',
                    # 'required': ['_id', 'name'],
                    'properties': {
                        '_id': {'bsonType': 'objectId'},
                        'name': {'bsonType': 'string'},
                    }
                }
            ]},
            'timestamp': {'bsonType': 'object'},
            'events': {
                'bsonType': 'array',
                'items': {'bsonType': 'object'}
            },
            'error': {'oneOf': [
                {'bsonType': 'null'},
                {
                    'bsonType': 'object',
                    'properties': {
                        'exception': {'bsonType': 'string'},
                        'exit_code': {'bsonType': 'int'},
                        'traceback': {'bsonType': 'string'},
                        'stderr': {'bsonType': 'string'}
                    }
                }
            ]},
        }
    }

    def __init__(self, database=None):
        if not database:
            database = Database()
        super().__init__(database, self._name)

    def initialize(self):
        self.create_index('status', name='status')
        self.create_index('schedule._id', name='schedule._id')
        self.create_index('schedule.name', name='schedule.name')
        self.create_index('timestamp.sent', name='timestamp.sent')
        self.create_index('timestamp.received', name='timestamp.received')
        self.create_index('timestamp.started', name='timestamp.started')
        self.create_index('timestamp.succeeded', name='timestamp.succeeded')
        self.create_index('timestamp.failed', name='timestamp.failed')

        self.database.command({'collMod': self._name, 'validator': {'$jsonSchema': self.schema}})


class Schedules(BaseCollection):
    def __init__(self):
        super().__init__(Database(), 'schedules')

    def initialize(self):
        self.create_index('name', name='name', unique=True)
        self.create_index('category', name='category')
        self.create_index('enabled', name='enabled')
        self.create_index('config.queue', name='config.queue')
        self.create_index('language.code', name='language.code')


class Workers(BaseCollection):
    def __init__(self):
        super().__init__(Database(), 'workers')
