from pymongo import MongoClient
from sshtunnel import SSHTunnelForwarder
from datetime import datetime
import pytz
import json


def main(client: MongoClient):
    schedules_collection = client['Zimfarm']['schedules']
    schedules = schedules_collection.find({"tags": ["nopic", "novid"]}, {"_id": 1, "name": 1})

    tasks = client['Zimfarm']['tasks']
    tasks_succeed = tasks.find({
        "timestamp.created": {
            '$gt': datetime(2019, 2, 1, 00, 00, 00, tzinfo=pytz.utc)
        }, "events.2.code": "succeeded"}, {'schedule_id': 1})
    schedules_id_succeed = [task['schedule_id'] for task in tasks_succeed]
    schedules_id_succeed = set(schedules_id_succeed)

    schedules_to_run = [schedule['name'] for schedule in schedules if schedule['_id'] not in schedules_id_succeed]
    print(len(schedules_to_run))
    encoded = json.dumps(schedules_to_run)
    print(encoded)




if __name__ == '__main__':
    with SSHTunnelForwarder('farm.openzim.org', ssh_username='chris', ssh_pkey="/Users/chrisli/.ssh/id_rsa",
                            remote_bind_address=('127.0.0.1', 27017), local_bind_address=('0.0.0.0', 27018)) as tunnel:
        with MongoClient(port=27018) as client:
            main(client)
    print('FINISH!')