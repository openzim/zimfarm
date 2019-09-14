import json
from unittest.mock import patch

import pytest
from bson import ObjectId

from common.enum import TaskStatus


class TestTaskCreate:
    @pytest.fixture(scope='session')
    def send_task(self):
        with patch('utils.celery.Celery.send_task_from_schedule') as mocked_send_task:
            yield mocked_send_task

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
    url = '/api/tasks/'

    def _assert_task(self, task, item):
        assert set(item.keys()) == {'_id', 'status', 'schedule'}
        assert item['_id'] == str(task['_id'])
        assert item['status'] == task['status']
        assert item['schedule']['_id'] == str(task['schedule']['_id'])
        assert item['schedule']['name'] == task['schedule']['name']

    @pytest.mark.parametrize('query_param',
                             [{'schedule_id': 'a'}, {'schedule_id': 123}])
    def test_bad_rquest(self, client, access_token, query_param):
        headers = {'Authorization': access_token, 'Content-Type': 'application/json'}
        response = client.get(self.url,
                              headers=headers,
                              query_string=query_param)
        assert response.status_code == 400

    def test_unauthorized(self, client, tasks):
        response = client.get(self.url)
        assert response.status_code == 401

    def test_list(self, client, access_token, tasks):
        tasks = [task for task in tasks if task['status'] not in [TaskStatus.sent, TaskStatus.received]]

        headers = {'Authorization': access_token, 'Content-Type': 'application/json'}
        response = client.get(self.url, headers=headers)
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['meta']['limit'] == 100
        assert data['meta']['skip'] == 0

        items = data['items']
        tasks.sort(key=lambda task: task['_id'], reverse=True)
        assert len(items) == len(tasks)
        for index, task in enumerate(tasks):
            item = items[index]
            self._assert_task(task, item)

    def test_list_pagination(self, client, access_token, tasks):
        url = '/api/tasks/?limit={}&skip={}'.format(10, 5)
        headers = {'Authorization': access_token, 'Content-Type': 'application/json'}
        response = client.get(url, headers=headers)
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['meta']['limit'] == 10
        assert data['meta']['skip'] == 5

    @pytest.mark.parametrize('statuses', [[TaskStatus.succeeded], [TaskStatus.succeeded, TaskStatus.received]])
    def test_status(self, client, access_token, tasks, statuses):
        url = f'/api/tasks/?'
        for status in statuses:
            url += f'status={status}&'

        headers = {'Authorization': access_token, 'Content-Type': 'application/json'}
        response = client.get(url, headers=headers)
        assert response.status_code == 200

        tasks = {task['_id']: task for task in tasks if task['status'] in statuses}
        items = json.loads(response.data)['items']

        assert len(tasks) == len(items)
        for item in items:
            task = tasks[ObjectId(item['_id'])]
            self._assert_task(task, item)

    def test_schedule_id(self, client, access_token, make_task):
        """Test list tasks with schedule id as filter"""

        # generate tasks with two schedule ids
        schedule_id, another_schedule_id = ObjectId(), ObjectId()
        for _ in range(5):
            make_task(schedule_id=schedule_id)
        for _ in range(10):
            make_task(schedule_id=another_schedule_id)

        # make request
        headers = {'Authorization': access_token, 'Content-Type': 'application/json'}
        response = client.get(self.url, headers=headers, query_string={'schedule_id': schedule_id})
        assert response.status_code == 200

        # check the correct number of schedule is returned
        items = json.loads(response.data)['items']
        assert len(items) == 5


class TestTaskGet:
    def test_unauthorized(self, client, task):
        url = '/api/tasks/{}'.format(task['_id'])
        response = client.get(url)
        assert response.status_code == 401

    def test_not_found(self, client, access_token):
        url = '/api/tasks/task_id'
        headers = {'Authorization': access_token, 'Content-Type': 'application/json'}
        response = client.get(url, headers=headers)
        assert response.status_code == 404

    def test_get(self, client, access_token, task):
        url = '/api/tasks/{}'.format(task['_id'])
        headers = {'Authorization': access_token, 'Content-Type': 'application/json'}
        response = client.get(url, headers=headers)
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['_id'] == str(task['_id'])
        assert data['status'] == task['status']
        assert data['schedule']['_id'] == str(task['schedule']['_id'])
        assert data['schedule']['name'] == task['schedule']['name']
        assert 'timestamp' in data
        assert 'events' in data


class TestTaskCancel:
    def test_unauthorized(self, client, task):
        url = '/api/tasks/{}/cancel'.format(task['_id'])
        response = client.post(url)
        assert response.status_code == 401

    def test_not_found(self, client, access_token):
        url = '/api/tasks/task_id/cancel'
        headers = {'Authorization': access_token, 'Content-Type': 'application/json'}
        response = client.post(url, headers=headers)
        assert response.status_code == 404

    @pytest.fixture(scope='session')
    def celery_ctrl(self):
        with patch('utils.celery.Celery.control') as mocked_celery_control:
            yield mocked_celery_control

    def test_wrong_statuses(self, client, access_token, tasks, celery_ctrl):
        for task in filter(lambda x: x['status'] not in TaskStatus.incomplete(), tasks):
            url = '/api/tasks/{}/cancel'.format(task['_id'])
            headers = {'Authorization': access_token,
                       'Content-Type': 'application/json'}
            response = client.post(url, headers=headers)
            assert response.status_code == 404

    def test_cancel_task(self, client, access_token, tasks, celery_ctrl):
        for task in filter(lambda x: x['status'] in TaskStatus.incomplete(), tasks):
            url = '/api/tasks/{}/cancel'.format(task['_id'])
            headers = {'Authorization': access_token,
                       'Content-Type': 'application/json'}
            response = client.post(url, headers=headers)
            assert response.status_code == 200
            celery_ctrl.revoke.assert_called_with(str(task['_id']), terminate=True)
