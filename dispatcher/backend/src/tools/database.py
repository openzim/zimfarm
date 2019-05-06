import json

from pymongo import MongoClient
from sshtunnel import SSHTunnelForwarder


def get_schedules_to_run():
    schedules = client['Zimfarm']['schedules']
    schedules = schedules.find({'most_recent_task.status': {'$ne': 'succeeded'}}, {'name': 1, 'language': 1})
    schedules = [schedule for schedule in schedules if 'f' <= schedule['language']['code'][0] <= 'g']
    schedule_names = [schedule['name'] for schedule in schedules]

    print(len(schedule_names))
    encoded = json.dumps(schedule_names)
    print(encoded)


if __name__ == '__main__':
    with SSHTunnelForwarder('farm.openzim.org', ssh_username='chris', ssh_pkey="/Users/chrisli/.ssh/id_rsa",
                            remote_bind_address=('127.0.0.1', 27017), local_bind_address=('0.0.0.0', 27018)) as tunnel:
        with MongoClient(port=27018) as client:
            get_schedules_to_run()
    print('FINISH!')
