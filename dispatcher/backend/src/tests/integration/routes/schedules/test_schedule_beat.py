import json

import pytest


class TestScheduleBeat:
    def test_get_no_access_token(self, client, schedule):
        """Test cannot get beat without access token"""

        url = '/api/schedules/{schedule}/beat'.format(schedule=str(schedule['_id']))
        response = client.get(url)
        assert response.status_code == 401

    def test_get_bad_schedule_id_or_name(self, client, access_token, schedule):
        """Test cannot get beat with a bad schedule id or name"""

        url = '/api/schedules/{schedule}/beat'.format(schedule='bad_schedule_id')
        response = client.get(url, headers={'Authorization': access_token})
        assert response.status_code == 404

    @pytest.mark.parametrize('body', [None, ''])
    def test_patch_bad_body(self, client, access_token, schedule, body):
        """Test cannot update beat with a bad request body"""

        url = '/api/schedules/{schedule}/beat'.format(schedule='bad_schedule_id')
        headers = {'Authorization': access_token, 'Content-Type': 'application/json'}
        response = client.patch(url, headers=headers, data=body)
        assert response.status_code == 400

    def test_patch_no_access_token(self, client, schedule):
        """Test cannot update beat without access token"""

        url = '/api/schedules/{schedule}/beat'.format(schedule=str(schedule['_id']))
        headers = {'Content-Type': 'application/json'}
        body = json.dumps({})
        response = client.patch(url, headers=headers, data=body)
        assert response.status_code == 401

    def test_patch_bad_schedule_id_or_name(self, client, access_token, schedule, make_beat_crontab):
        """Test cannot update beat with a bad schedule id or name"""

        url = '/api/schedules/{schedule}/beat'.format(schedule='bad_schedule_id')
        headers = {'Authorization': access_token, 'Content-Type': 'application/json'}
        body = json.dumps(make_beat_crontab(hour='3'))
        response = client.patch(url, headers=headers, data=body)
        assert response.status_code == 404

    def test_get_beat_crontab(self, client, access_token, schedule):
        """Test get crontab beat"""

        schedule_id = schedule['_id']
        url = '/api/schedules/{schedule}/beat'.format(schedule=str(schedule_id))
        response = client.get(url, headers={'Authorization': access_token})
        assert response.status_code == 200
        assert schedule['beat'] == response.get_json()

        schedule_name = schedule['name']
        url = '/api/schedules/{schedule}/beat'.format(schedule=str(schedule_name))
        response = client.get(url, headers={'Authorization': access_token})
        assert response.status_code == 200
        assert schedule['beat'] == response.get_json()

    def test_update_beat_crontab(self, client, access_token, make_beat_crontab, make_schedule):
        """Test """
