import json
import pytest
from unittest.mock import patch


@pytest.fixture(scope='session')
def send_task():
    with patch('models.ScheduleService.send_task') as mocked_send_task:
        yield mocked_send_task


class TestTaskCreate:
    @pytest.fixture()
    def schedule(self, make_schedule):
        schedule = make_schedule('wikipedia_en')
        return schedule

    def test_create_from_schedule(self, client, access_token, schedule, send_task):
        url = '/api/tasks/'
        headers = {'Authorization': access_token, 'Content-Type': 'application/json'}
        data = json.dumps({'schedule_names': [schedule.get('name')]})
        response = client.post(url, headers=headers, data=data)
        assert response.status_code == 200

        send_task.assert_called_with(schedule['name'])

    @pytest.mark.parametrize('body', [
        None, '', '[]', '{"test": 123}'
    ])
    def test_create_with_bad_body(self, client, access_token, body):
        url = '/api/tasks/'
        response = client.post(url, headers={'Authorization': access_token}, data=body)
        assert response.status_code == 400


class TestTaskList:
    pass