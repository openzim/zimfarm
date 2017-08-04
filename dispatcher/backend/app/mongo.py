from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection


class Client(MongoClient):
    def __init__(self):
        super().__init__(host='mongo')


class ZimfarmDatabase(Database):
    def __init__(self):
        super().__init__(Client(), 'Zimfarm')

    def initialize(self):
        names = self.collection_names(include_system_collections=False)

        def create_tasks():
            if 'tasks' in names:
                return
            self.create_collection('tasks', validator={
                '$and': [
                    {'celery_task_name': {'$type': 'string'}},
                    {'status': {'$in': ['PENDING', 'PREPARING', 'GENERATING', 'UPLOADING', 'FINISHED', 'ERROR']}},
                    {'$and': [
                        {'time_stamp.created': {'$exists': True}},
                        {'time_stamp.started': {'$exists': True}},
                        {'time_stamp.ended': {'$exists': True}},
                    ]},
                    {'$or': [
                        {'options': {'$exists': True}}
                    ]},
                    {'$or': [
                        {'steps': {'$elemMatch': {'name': {'$type': 'string'}}}},
                        {'steps': {'$size': 0}}
                    ]}
                ]
            })

        def create_users():
            if 'users' in names:
                return
            self.create_collection('users', validator={
                '$and': [
                    {'username': {'$type': 'string'}},
                    {'password_hash': {'$type': 'string'}}
                ]
            })

        create_tasks()
        create_users()


class TasksCollection(Collection):
    def __init__(self):
        super().__init__(ZimfarmDatabase(), 'tasks')


class UsersCollection(Collection):
    def __init__(self):
        super().__init__(ZimfarmDatabase(), 'users')
