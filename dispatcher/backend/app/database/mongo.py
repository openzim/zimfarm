from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from pymongo import TEXT


class Client(MongoClient):
    def __init__(self):
        super().__init__(host='mongo')


class ZimfarmDatabase(Database):
    def __init__(self):
        super().__init__(Client(), 'Zimfarm')

    def initialize(self):
        names = self.collection_names(include_system_collections=False)
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
                    {'options.mwoffliner': {'$exists': True}}
                ]},
                {'$or': [
                    {'stages': {'$elemMatch': {'name': {'$type': 'string'}, 'success': {'$type': 'bool'}}}},
                    {'stages': {'$size': 0}}
                ]}
            ]
        })


class TasksCollection(Collection):
    def __init__(self):
        super().__init__(ZimfarmDatabase(), 'tasks')

    # not working
    # def initialize(self):
    #     for _, value in self.index_information().items():
    #         index_keys = [key[0] for key in value['key']]
    #         if 'celery_task_name' not in index_keys:
    #         if 'status' not in index_keys:
    #             self.create_index([('status', TEXT)])
