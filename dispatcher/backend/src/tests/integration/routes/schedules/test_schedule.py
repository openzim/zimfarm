import pytest


class TestScheduleList:
    def test_list_schedules_no_param(self, client, access_token, schedules):
        """Test list schedules"""

        url = '/api/schedules/'
        response = client.get(url, headers={'Authorization': access_token})
        assert response.status_code == 200

        response_json = response.get_json()
        assert 'items' in response_json
        assert len(response_json['items']) == 20
        for item in response_json['items']:
            assert isinstance(item['_id'], str)
            assert isinstance(item['category'], str)
            assert isinstance(item['enabled'], bool)
            assert isinstance(item['name'], str)
            assert isinstance(item['config']['queue'], str)
            assert isinstance(item['language']['code'], str)
            assert isinstance(item['language']['name_en'], str)
            assert isinstance(item['language']['name_native'], str)
            assert isinstance(item['tags'], list)

    @pytest.mark.parametrize('skip, limit, expected', [
        (0, 30, 30), (10, 15, 15), (40, 25, 10), (100, 100, 0), ('', 10, 10), (5, 'abc', 20)
    ])
    def test_list_schedules_with_param(self, client, access_token, schedules, skip, limit, expected):
        """Test list schedules"""

        url = '/api/schedules/?skip={}&limit={}'.format(skip, limit)
        response = client.get(url, headers={'Authorization': access_token})
        assert response.status_code == 200

        response_json = response.get_json()
        assert 'items' in response_json
        assert len(response_json['items']) == expected

    def test_unauthorized(self, client):
        url = '/api/schedules/'
        response = client.get(url)
        assert response.status_code == 401
        assert response.get_json() == {'error': 'token invalid'}


class TestScheduleGet:
    def test_get_schedule_with_id(self, client, access_token, schedule):
        """Test get schedule with id"""

        url = '/api/schedules/{}'.format(schedule['_id'])
        response = client.get(url, headers={'Authorization': access_token})
        assert response.status_code == 200

        schedule['_id'] = str(schedule['_id'])
        assert response.get_json() == schedule

    def test_get_schedule_with_name(self, client, access_token, schedule):
        """Test get schedule with name"""

        url = '/api/schedules/{}'.format(schedule['name'])
        response = client.get(url, headers={'Authorization': access_token})
        assert response.status_code == 200

        schedule['_id'] = str(schedule['_id'])
        assert response.get_json() == schedule

    def test_unauthorized(self, client, access_token, schedule):
        url = '/api/schedules/{}'.format(schedule['name'])
        response = client.get(url)
        assert response.status_code == 401
        assert response.get_json() == {'error': 'token invalid'}