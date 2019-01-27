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
