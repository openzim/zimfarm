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

    def test_schedule_is_not_requested(self, client, headers, temp_schedule):
        # check in GET /schedules/{schedule_name}
        url = f"/schedules/{temp_schedule['name']}"
        response = client.get(
            url,
            headers=headers,
        )
        assert response.status_code == 200
        assert "is_requested" in response.json
        assert response.json["is_requested"] is False

        # check in GET /schedules
        url = "/schedules/"
        response = client.get(
            url,
            headers=headers,
        )
        assert response.status_code == 200
        assert "items" in response.json
        for item in response.json["items"]:
            if item["name"] != temp_schedule["name"]:
                continue
            assert "is_requested" in item
            assert item["is_requested"] is False

    def test_schedule_is_requested(
        self, client, headers, temp_schedule, temp_requested_task
    ):
        # check in GET /schedules/{schedule_name}
        url = f"/schedules/{temp_schedule['name']}"
        response = client.get(
            url,
            headers=headers,
        )
        assert response.status_code == 200
        assert "is_requested" in response.json
        assert response.json["is_requested"] is True

        # check in GET /schedules
        url = "/schedules/"
        response = client.get(
            url,
            headers=headers,
        )
        assert response.status_code == 200
        assert "items" in response.json
        for item in response.json["items"]:
            if item["name"] != temp_schedule["name"]:
                continue
            assert "is_requested" in item
            assert item["is_requested"] is True
