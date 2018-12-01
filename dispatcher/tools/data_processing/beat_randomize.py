import requests
from random import randint


def randomize(token: str):
    response = requests.get('https://farm.openzim.org/api/schedules/',
                            params={'limit': 150}, headers={'token': token})

    assert response.status_code == 200
    response_json = response.json()
    schedule_names = [schedule['name'] for schedule in response_json['items']]

    for name in schedule_names:
        config = {
            'minute': randint(0, 3) * 15,
            'hour': randint(0, 23),
            'day_of_month': randint(0, 28)
        }
        request_json = {
            'type': 'crontab',
            'config': config
        }
        url = 'https://farm.openzim.org/api/schedules/{}/beat'.format(name)
        response = requests.patch(url, headers={'token': token}, json=request_json)
        print('{}, status_code={}'.format(name, response.status_code))


randomize(token='')