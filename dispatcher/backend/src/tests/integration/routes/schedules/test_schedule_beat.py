import json

import pytest


class TestScheduleBeatGet:
    def test_beat_crontab(self, client, access_token, schedule):
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

    def test_no_access_token(self, client, schedule):
        """Test cannot get beat without access token"""

        url = '/api/schedules/{schedule}/beat'.format(schedule=str(schedule['_id']))
        response = client.get(url)
        assert response.status_code == 401

    def test_bad_schedule_id_or_name(self, client, access_token, schedule):
        """Test cannot get beat with a bad schedule id or name"""

        url = '/api/schedules/{schedule}/beat'.format(schedule='bad_schedule_id')
        response = client.get(url, headers={'Authorization': access_token})
        assert response.status_code == 404


class TestScheduleBeatUpdate:
    def test_update_beat_crontab_full(self, client, access_token, make_beat_crontab, make_schedule):
        """Test update crontab beat"""

        schedule = make_schedule('name', 'wikipedia')
        url = '/api/schedules/{schedule}/beat'.format(schedule=str(schedule['_id']))
        beat = make_beat_crontab(minute='30', hour='7', day_of_month='20')

        # update beat
        headers = {'Authorization': access_token, 'Content-Type': 'application/json'}
        response = client.patch(url, headers=headers, data=json.dumps(beat))
        assert response.status_code == 200

        # check updated value
        response = client.get(url, headers={'Authorization': access_token})
        assert response.status_code == 200
        assert beat == response.get_json()

    def test_update_beat_crontab_partial(self, client, access_token, make_beat_crontab, make_schedule):
        """Test partial update crontab beat"""

        schedule = make_schedule('name', 'wikipedia')
        url = '/api/schedules/{schedule}/beat'.format(schedule=str(schedule['_id']))
        beat = make_beat_crontab(day_of_month='10')

        # partial update
        partial_beat = {'type': 'crontab', 'config': {'day_of_month': '10'}}
        headers = {'Authorization': access_token, 'Content-Type': 'application/json'}
        response = client.patch(url, headers=headers, data=json.dumps(partial_beat))
        assert response.status_code == 200

        # check updated value
        response = client.get(url, headers={'Authorization': access_token})
        assert response.status_code == 200
        assert beat == response.get_json()

    @pytest.mark.parametrize('body', [
        None, '', 'bad_body', '{"type": "bad_type", "config": {}}', '{"type": "bad_type", "config": null}'
    ])
    def test_bad_body(self, client, access_token, schedule, body):
        """Test cannot update beat with a bad request body"""

        url = '/api/schedules/{schedule}/beat'.format(schedule=str(schedule['_id']))
        headers = {'Authorization': access_token, 'Content-Type': 'application/json'}
        response = client.patch(url, headers=headers, data=body)
        assert response.status_code == 400

    @pytest.mark.parametrize('update', [{'hour': ''}, {'day_of_month': '*//4'}])
    def test_bad_crontab(self, client, access_token, schedule, make_beat_crontab, update):
        """Test cannot update beat with a bad crontab"""

        beat = make_beat_crontab(minute='30', hour='7', day_of_month='20')
        beat['config'].update(update)
        url = '/api/schedules/{schedule}/beat'.format(schedule=str(schedule['_id']))
        headers = {'Authorization': access_token, 'Content-Type': 'application/json'}
        response = client.patch(url, headers=headers, data=json.dumps(beat))
        assert response.status_code == 400

    def test_bad_content_type(self, client, access_token, schedule, make_beat_crontab):
        """Test cannot update beat with a bad content type"""

        beat = make_beat_crontab(minute='30', hour='7', day_of_month='20')
        url = '/api/schedules/{schedule}/beat'.format(schedule=str(schedule['_id']))
        headers = {'Authorization': access_token}
        response = client.patch(url, headers=headers, data=json.dumps(beat))
        assert response.status_code == 400

    def test_patch_no_access_token(self, client, schedule, make_beat_crontab):
        """Test cannot update beat without access token"""

        beat = make_beat_crontab(minute='30', hour='7', day_of_month='20')
        url = '/api/schedules/{schedule}/beat'.format(schedule=str(schedule['_id']))
        headers = {'Content-Type': 'application/json'}
        response = client.patch(url, headers=headers, data=json.dumps(beat))
        assert response.status_code == 401

    def test_patch_bad_schedule_id_or_name(self, client, access_token, make_beat_crontab):
        """Test cannot update beat with a bad schedule id or name"""

        beat = make_beat_crontab(minute='30', hour='7', day_of_month='20')
        url = '/api/schedules/{schedule}/beat'.format(schedule='bad_schedule_id')
        headers = {'Authorization': access_token, 'Content-Type': 'application/json'}
        response = client.patch(url, headers=headers, data=json.dumps(beat))
        assert response.status_code == 404
