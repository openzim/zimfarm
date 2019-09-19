import pytest
from bson import ObjectId


class TestUpdateScheduleConfig:
    @pytest.mark.parametrize('data', [{}, {'field': 123}])
    def test_bad_payload(self, client, access_token, schedule, data):
        schedule_id = schedule['_id']
        url = f'/api/schedules/{schedule_id}/config/'
        response = client.patch(url, headers={'Authorization': access_token}, data=data)
        assert response.status_code == 400

    @pytest.mark.parametrize('schedule_id', ['123', ObjectId()])
    def test_not_found(self, client, access_token, schedule_id):
        url = f'/api/schedules/{schedule_id}/config/'
        response = client.patch(url, headers={'Authorization': access_token}, data={})
        assert response.status_code == 404
