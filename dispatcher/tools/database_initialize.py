from collections import OrderedDict

from pymongo import MongoClient
from pymongo.database import Database


def initialize_schedule(database: Database):
    if 'schedules' not in database.list_collection_names():
        database.create_collection('schedules')

    json_schema = {
        'bsonType': 'object',
        'required': ['name', 'category', 'enabled'],
        'properties': {
            'name': {
                'bsonType': 'string',
                'description': 'name of the schedule'
            },
            'category': {
                'bsonType': 'string',
                'description': 'category of the schedule'
            },
            'enabled': {
                'bsonType': 'bool',
                'description': 'if the schedule is enabled'
            },
            'last_run': {
                'bsonType': 'date',
                'description': 'last time the schedule is run'
            },
            'total_run': {
                'bsonType': 'int',
                'description': 'total time the schedule has run'
            }
        }
    }

    query = [('collMod', 'schedules'),
             ('validator', {'$jsonSchema': json_schema}),
             ('validationLevel', 'moderate')]
    query = OrderedDict(query)
    database.command(query)


def initialize(client: MongoClient):
    database = client.Zimfarm
    initialize_schedule(database)


if __name__ == '__main__':
    client = MongoClient()
    initialize(client)