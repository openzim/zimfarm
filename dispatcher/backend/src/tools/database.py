from pymongo import MongoClient
from sshtunnel import SSHTunnelForwarder
from datetime import datetime
import pytz
import json


def get_schedule_to_run_json(client: MongoClient):
    schedules_collection = client['Zimfarm']['schedules']

    tasks = client['Zimfarm']['tasks']
    tasks_succeed = tasks.find({
        "timestamp.succeeded": {
            '$gte': datetime(2019, 3, 1, 00, 00, 00, tzinfo=pytz.utc)
        }, "files": {"$exists": True}}, {'schedule_id': 1})
    schedules_id_succeed = [task.get('schedule_id') for task in tasks_succeed]
    schedules_id_succeed = set(schedules_id_succeed)

    schedules = schedules_collection.find({"tags": ["nopic", "novid"]}, {"_id": 1, "name": 1, "language.code": 1})
    schedules_to_run = [schedule for schedule in schedules
                        if schedule['_id'] not in schedules_id_succeed]
    schedules_to_run = [schedule for schedule in schedules_to_run if 'e' <= schedule['language']['code'][0] < 'n']
    schedules_to_run = [schedule['name'] for schedule in schedules_to_run]
    print(len(schedules_to_run))
    encoded = json.dumps(schedules_to_run)
    print(encoded)


def update_most_recent_task(client: MongoClient):
    tasks = client['Zimfarm']['tasks']
    for task in tasks.find({}):
        schedule_id = task.get('schedule_id')
        schedule_name = task.get('schedule_name')
        schedule_filter = {'_id': schedule_id} if schedule_id else {'name': schedule_name}

        events = task.get('events', [])
        if events:
            event = events[-1]
            update = {'$set': {'most_recent_task': {'_id': task['_id'],
                                                    'status': event['code'],
                                                    'updated_at': event['timestamp']}}}
            client['Zimfarm']['schedules'].update_one(schedule_filter, update)


def fix(client: MongoClient):
    tasks = client['Zimfarm']['tasks']
    schedules = client['Zimfarm']['schedules']
    for task in tasks.find({}):
        if 'schedule_id' in task:
            schedule_id = task['schedule_id']
            schedule = schedules.find_one({'_id': schedule_id})
        elif 'schedule_name' in task:
            schedule_name = task['schedule_name']
            schedule = schedules.find_one({'name': schedule_name})
        else:
            continue

        if schedule is None:
            print(task)
            continue

        tasks.update_one({'_id': task['_id']}, {
            '$set': {'schedule': {'_id': schedule['_id'], 'name': schedule['name']}},
            '$unset': {'schedule_id': 1, 'schedule_name': 1}
        })


if __name__ == '__main__':
    with SSHTunnelForwarder('farm.openzim.org', ssh_username='chris', ssh_pkey="/Users/chrisli/.ssh/id_rsa",
                            remote_bind_address=('127.0.0.1', 27017), local_bind_address=('0.0.0.0', 27018)) as tunnel:
        with MongoClient(port=27018) as client:
            fix(client)
    print('FINISH!')
