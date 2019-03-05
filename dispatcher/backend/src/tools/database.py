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
    schedules_id_succeed = [task['schedule_id'] for task in tasks_succeed]
    schedules_id_succeed = set(schedules_id_succeed)

    schedules = schedules_collection.find({"tags": ["nopic", "novid"]}, {"_id": 1, "name": 1, "language.code": 1})
    schedules_to_run = [schedule for schedule in schedules
                        if schedule['_id'] not in schedules_id_succeed]
    schedules_to_run = [schedule for schedule in schedules_to_run if 'e' <= schedule['language']['code'][0] < 'n']
    schedules_to_run = [schedule['name'] for schedule in schedules_to_run]
    print(len(schedules_to_run))
    encoded = json.dumps(schedules_to_run)
    print(encoded)


def assemble_manual_run_request(client: MongoClient):
    schedules_collection = client['Zimfarm']['schedules']
    schedules = schedules_collection.find({"category": "wikiversity", "tags": ["nopic", "novid"]},
                                          {"_id": 1, "name": 1})
    schedule_names = [schedule['name'] for schedule in schedules]
    encoded = json.dumps(schedule_names)
    print(encoded)


def nopic_to_nopic_and_novid(client: MongoClient):
    schedules_collection = client['Zimfarm']['schedules']
    schedules = schedules_collection.find({"category": "wikipedia", "tags": ["nopic"]}, {"_id": 1, "name": 1})

    update_count = 0
    for schedule in schedules:
        schedule_id = schedule['_id']
        schedule_name = schedule['name'].replace('_nopic', '')
        result = schedules_collection.update_one(
            {'_id': schedule_id},
            {'$set': {
                'name': schedule_name,
                'config.queue': 'large',
                'config.flags.useCache': True,
                'config.flags.format': ["nopic", "novid"],
                'tags': ["nopic", "novid"]}})
        update_count += result.modified_count
    print(f"Update count: {update_count}")


def remove_duplicated_novid_schedule(client: MongoClient):
    schedules_collection = client['Zimfarm']['schedules']
    schedules = schedules_collection.find({"tags": ["nopic", "novid"]}, {"category": 1, "language": 1})

    delete_count = 0
    for schedule in schedules:
        result = schedules_collection.delete_one({
            'category': schedule['category'],
            'language.code': schedule['language']['code'],
            'tags': ['novid']})
        delete_count += result.deleted_count
    print(f"Delete count: {delete_count}")


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



if __name__ == '__main__':
    with SSHTunnelForwarder('farm.openzim.org', ssh_username='chris', ssh_pkey="/Users/chrisli/.ssh/id_rsa",
                            remote_bind_address=('127.0.0.1', 27017), local_bind_address=('0.0.0.0', 27018)) as tunnel:
        with MongoClient(port=27018) as client:
            update_most_recent_task(client)
    print('FINISH!')
