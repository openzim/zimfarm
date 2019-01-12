from collections import OrderedDict

from pymongo import MongoClient
from pymongo.database import Database


def initialize_schedule(database: Database):
    if 'schedules' not in database.list_collection_names():
        database.create_collection('schedules')

    json_schema = {
        'bsonType': 'object',
        'required': ['name', 'category', 'enabled', 'tags'],
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
            'tags': {
                'bsonType': 'array',
                'description': 'an array of schedule tags',
                'items': {
                    'bsonType': 'string',
                    'enum': ['nodet', 'nopic', 'novid']
                }
            },
            'last_run': {
                'bsonType': 'date',
                'description': 'last time the schedule is run'
            },
            'total_run': {
                'bsonType': 'int',
                'description': 'total time the schedule has run'
            },
            'beat': {
                'bsonType': 'object',
                'description': 'schedule beat',
                'required': ['type', 'config'],
                'properties': {
                    'type': {
                        'bsonType': 'string',
                        'enum': ['crontab']
                    },
                    'config': {
                        'bsonType': 'object',
                        'required': ['minute', 'hour', 'day_of_month', 'day_of_week', 'month_of_year'],
                        'properties': {
                            'minute': {'bsonType': 'string'},
                            'hour': {'bsonType': 'string'},
                            'day_of_month': {'bsonType': 'string'},
                            'day_of_week': {'bsonType': 'string'},
                            'month_of_year': {'bsonType': 'string'}
                        }
                    }
                }
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