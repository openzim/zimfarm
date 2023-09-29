import json

import pytest


class TestRequestedTaskBusiness:
    @pytest.fixture(scope="module")
    def headers(self, access_token):
        return {"Authorization": access_token, "Content-Type": "application/json"}

    @pytest.fixture
    def temp_requested_task(self, client, headers, temp_schedule):
        response = client.post(
            "/requested-tasks/",
            headers=headers,
            data=json.dumps({"schedule_names": [temp_schedule["name"]]}),
        )
        assert response.status_code == 201
        assert "requested" in response.json
        assert len(response.json["requested"]) == 1
        requested_task_id = response.json["requested"][0]
        yield requested_task_id

        response = client.delete(
            f"/requested-tasks/{requested_task_id}",
            headers=headers,
        )
        assert response.status_code == 200

    def test_requested_task_with_schedule(
        self, client, headers, temp_schedule, temp_requested_task
    ):
        url = f"/requested-tasks/{temp_requested_task}"
        response = client.get(
            url,
            headers=headers,
        )
        assert response.status_code == 200
        assert "schedule_name" in response.json
        assert response.json["schedule_name"] == temp_schedule["name"]
        assert "original_schedule_name" in response.json
        assert response.json["original_schedule_name"] == temp_schedule["name"]

    def test_requested_task_without_schedule(
        self, client, headers, temp_schedule, temp_requested_task
    ):
        url = f"/schedules/{temp_schedule['name']}"
        response = client.delete(
            url,
            headers=headers,
        )
        assert response.status_code == 204
        url = f"/requested-tasks/{temp_requested_task}"
        response = client.get(
            url,
            headers=headers,
        )
        assert response.status_code == 200
        assert "schedule_name" in response.json
        assert response.json["schedule_name"] == "none"
        assert "original_schedule_name" in response.json
        assert response.json["original_schedule_name"] == temp_schedule["name"]
