

class TestListSchedule:
    url = '/api/schedules/'

    def test_unauthorized(self, client):
        response = client.get(self.url)
        assert response.status_code == 401

    def test_success(self, client, access_token):
        response = client.get(self.url, headers={'Authorization': access_token})
        assert response.status_code == 200

        response_json = response.get_json()
        assert 'items' in response_json
        assert 'meta' in response_json
