import os

from pymongo import MongoClient
from pymongo.collection import Collection as BaseCollection
from pymongo.database import Database as BaseDatabase


class Client(MongoClient):
    def __init__(self):
        super().__init__(host=os.getenv('MONGO_HOST'), port=int(os.getenv('MONGO_PORT')))


class Database(BaseDatabase):
    def __init__(self):
        super().__init__(Client(), 'Zimfarm')


class Workers(BaseCollection):
    def __init__(self):
        super().__init__(Database(), 'workers')
