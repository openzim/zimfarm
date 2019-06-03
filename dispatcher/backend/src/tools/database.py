import os
import json
import getpass
from datetime import datetime

from pymongo import MongoClient
from sshtunnel import SSHTunnelForwarder


def get_schedules_to_run(query: dict):
    schedules = client['Zimfarm']['schedules']
    schedules = schedules.find(query, {'name': 1, 'language': 1})
    schedules = [schedule for schedule in schedules if 'a' <= schedule['language']['code'][0] <= 'g']
    schedule_names = [schedule['name'] for schedule in schedules]

    print(len(schedule_names))
    encoded = json.dumps(schedule_names)
    print(encoded)


if __name__ == '__main__':
    ssh_pkey = os.getenv('ZIMFARM_KEYPATH',
                         os.path.abspath(os.path.expanduser('~/.ssh/id_rsa')))
    ssh_username = os.getenv('ZIMFARM_USERNAME', getpass.getuser())

    with SSHTunnelForwarder('farm.openzim.org', ssh_username=ssh_username, ssh_pkey=ssh_pkey,
                            remote_bind_address=('127.0.0.1', 27017), local_bind_address=('0.0.0.0', 27018)) as tunnel:
        with MongoClient(port=27018) as client:
            has_not_run_this_month = {'most_recent_task.updated_at': {'$lt': datetime(year=2019, month=6, day=1)}}
            not_succeeded = {'most_recent_task.status': {'$ne': 'succeeded'}}

            get_schedules_to_run(query=has_not_run_this_month)
    print('FINISH!')
