class TestScheduleConfigUpdate:
    def test_authorized(self, client, schedule):
        """Test attempting to update schedule config without authorization returns 401"""

        url = f'/api/schedules/{schedule["_id"]}/config/'
        response = client.patch(url)
        assert response.status_code == 401

    def test_update_mwoffliner(self):
        pass