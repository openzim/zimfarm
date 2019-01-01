from pymongo import MongoClient
from pymongo.database import Database as BaseDatabase
from pymongo.collection import Collection as BaseCollection


class Client(MongoClient):
    def __init__(self):
        super().__init__(host='mongo')


class Database(BaseDatabase):
    def __init__(self):
        super().__init__(Client(), 'Zimfarm')


class Schedules(BaseCollection):
    def __init__(self):
        super().__init__(Database(), 'schedules')


class Tasks(BaseCollection):
    def __init__(self):
        super().__init__(Database(), 'tasks')