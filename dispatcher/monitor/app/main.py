import os
import sys
from datetime import datetime

from celery import Celery
from bson.objectid import ObjectId
from pymongo import MongoClient, database, collection


class Client(MongoClient):
    def __init__(self):
        super().__init__(host='mongo')


class Database(database.Database):
    def __init__(self):
        super().__init__(Client(), 'Zimfarm')


class Tasks(collection.Collection):
    def __init__(self):
        super().__init__(Database(), 'tasks')


class TaskEvents(collection.Collection):
    def __init__(self):
        super().__init__(Database(), 'task_events')


def process_event(event: dict):
    type_parts = event.get('type', '-').split('-')
    if type_parts[0] != 'task':
        return

    if 'uuid' in event:
        event['uuid'] = ObjectId(event['uuid'])

    update_set = {}

    status = type_parts[1]
    if status == 'logs':
        update_set['logs'] = event['logs']
    else:
        update_set['status'] = status.upper()

    if status == 'succeeded' or status == 'failed':
        if 'timestamp' in event:
            termination_time = datetime.fromtimestamp(event['timestamp'])
            update_set['timestamp.termination'] = termination_time

    Tasks().update_one({'_id': event['uuid']}, {'$set': update_set})
    TaskEvents().insert_one(event)


if __name__ == '__main__':
    try:
        system_username = 'system'
        system_password = os.getenv('SYSTEM_PASSWORD', '')
        url = 'amqp://{username}:{password}@rabbit:5672/'.format(username=system_username,
                                                                          password=system_password)
        celery = Celery(broker=url)
        with celery.connection() as connection:
            recv = celery.events.Receiver(connection, handlers={'*': process_event})
            recv.capture(limit=None, timeout=None, wakeup=True)
    except (KeyboardInterrupt, SystemExit):
        print('\n',
              'Interrupted', sep='')
        sys.exit()
