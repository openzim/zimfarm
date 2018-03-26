import sys
import json

from celery import Celery
from bson.objectid import ObjectId
from pymongo import MongoClient, database, collection


class Client(MongoClient):
    def __init__(self):
        super().__init__(host='mongo')


class Database(database.Database):
    def __init__(self):
        super().__init__(Client(), 'Zimfarm')


class TaskEvents(collection.Collection):
    def __init__(self):
        super().__init__(Database(), 'task_events')


def process_event(event):
    if 'type' in event and 'task' in event['type']:
        if 'uuid' in event:
            event['uuid'] = ObjectId(event['uuid'])
        print(event)
        # if 'result' in event:
        #     event['result'] = json.loads(event['result'][1:-1])
        events = TaskEvents()
        events.insert_one(event)


if __name__ == '__main__':
    try:
        url = 'amqp://{username}:{password}@{host}:{port}/zimfarm'.format(username='admin', password='admin_passes',
                                                                           host='rabbit', port=5672)
        celery = Celery(broker=url)
        state = celery.events.State()

        with celery.connection() as connection:
            recv = celery.events.Receiver(connection, handlers={'*': process_event})
            recv.capture(limit=None, timeout=None, wakeup=True)
    except (KeyboardInterrupt, SystemExit):
        print('\n',
              'Interrupted', sep='')
        sys.exit()
