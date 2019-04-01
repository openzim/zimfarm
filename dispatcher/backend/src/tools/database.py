from pymongo import MongoClient
from sshtunnel import SSHTunnelForwarder
from datetime import datetime
import pytz
import json


def get_succeed_task_schedule_ids(client: MongoClient) -> set:
    tasks = client['Zimfarm']['tasks']
    tasks_sent = tasks.find({'timestamp.succeeded': {'$gte': datetime(2019, 4, 1, 00, 00, 00, tzinfo=pytz.utc)},
                             'files': {'$exists': True}},
                            {'schedule': 1})
    return set([task['schedule']['_id'] for task in tasks_sent])


def get_sent_task_schedule_ids(client: MongoClient) -> set:
    tasks = client['Zimfarm']['tasks']
    tasks_sent = tasks.find({'timestamp.sent': {'$gte': datetime(2019, 4, 1, 00, 00, 00, tzinfo=pytz.utc)}},
                            {'schedule': 1})
    return set([task['schedule']['_id'] for task in tasks_sent])


def get_schedules_to_run(schedules_excluded: set):
    schedules = client['Zimfarm']['schedules']
    schedules = schedules.find({}, {'name': 1, 'language': 1})
    schedules = [schedule for schedule in schedules if schedule['_id'] not in schedules_excluded]
    schedules = [schedule for schedule in schedules if 'a' <= schedule['language']['code'][0] <= 'a']
    schedule_names = [schedule['name'] for schedule in schedules]

    print(len(schedule_names))
    encoded = json.dumps(schedule_names)
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


def get_most_recent_failed_task(client: MongoClient):
    import re

    tasks = client['Zimfarm']['tasks']
    schedules = client['Zimfarm']['schedules']
    schedules_to_tun = []
    for schedule in schedules.find({'most_recent_task.status': 'failed'}):
        schedule_name = schedule['name']
        task = tasks.find_one({'_id': schedule['most_recent_task']['_id']})
        events = task.get('events', [])
        traceback = events[-1]['traceback']

        reg = re.compile(r'non-zero exit status (\d*): ')
        result = reg.search(traceback)
        if result:
            code = result.group(1)
        else:
            schedules_to_tun.append(schedule_name)

        # with open(f'traceback/{code}_{schedule_name}.log', 'w') as file:
        #     file.write(traceback.replace('\\n', '\n'))

    print(json.dumps(schedules_to_tun))


if __name__ == '__main__':
    with SSHTunnelForwarder('farm.openzim.org', ssh_username='chris', ssh_pkey="/Users/chrisli/.ssh/id_rsa",
                            remote_bind_address=('127.0.0.1', 27017), local_bind_address=('0.0.0.0', 27018)) as tunnel:
        with MongoClient(port=27018) as client:
            excluded = get_sent_task_schedule_ids(client)
            get_schedules_to_run(excluded)
    print('FINISH!')
