from pymongo import MongoClient
from pymongo.collection import Collection as BaseCollection
from pymongo.database import Database as BaseDatabase


class Client(MongoClient):
    def __init__(self):
        super().__init__(host='mongo')


class Database(BaseDatabase):
    def __init__(self):
        super().__init__(Client(), 'Zimfarm')


class Workers(BaseCollection):
    def __init__(self):
        super().__init__(Database(), 'workers')


class Tasks(BaseCollection):
    def __init__(self):
        super().__init__(Database(), 'tasks')
