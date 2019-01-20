import json
import pytest
from unittest.mock import patch


@pytest.fixture(scope='session')
def celery():
    with patch('routes.tasks.task.Celery') as mocked_celery:
        yield mocked_celery.return_value


class TestTaskCreate:
    def test_create_from_schedule(self, client, access_token, schedule, celery):
        url = '/api/tasks/'
        headers = {'Authorization': access_token, 'Content-Type': 'application/json'}
        data = json.dumps({'schedule_name': schedule.get('name')})
        response = client.post(url, headers=headers, data=data)
        assert response.status_code == 200

        celery.send_task.assert_called_once()


    @pytest.mark.parametrize('body', [
        None, '', '[]', '{"test": 123}'
    ])
    def test_create_with_bad_body(self, client, access_token, body):
        url = '/api/tasks/'
        response = client.post(url, headers={'Authorization': access_token}, data=body)
        assert response.status_code == 400

