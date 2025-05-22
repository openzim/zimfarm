import pytest

SCHEDULE_NAME = "a_schedule_for_tasks"


class TestTaskBusiness:
    @pytest.fixture(scope="module")
    def headers(self, access_token):
        return {"Authorization": access_token, "Content-Type": "application/json"}

    @pytest.fixture(scope="module")
    def task(self, client, headers, worker, make_requested_task, garbage_collector):
        requested_task = make_requested_task(SCHEDULE_NAME)
        url = "/tasks/{}".format(str(requested_task["_id"]))
        response = client.post(
            url, headers=headers, query_string={"worker_name": "worker_name"}
        )
        assert response.status_code == 201
        assert "_id" in response.json
        task_id = response.json["_id"]
        garbage_collector.add_task_id(task_id)
        yield task_id

    def test_task_with_schedule(self, client, headers, task):
        url = f"/tasks/{task}"
        response = client.get(
            url,
            headers=headers,
        )
        assert response.status_code == 200
        assert "schedule_name" in response.json
        assert response.json["schedule_name"] == SCHEDULE_NAME
        assert "original_schedule_name" in response.json
        assert response.json["original_schedule_name"] == SCHEDULE_NAME

    def test_task_without_schedule(self, client, headers, task):
        url = f"/schedules/{SCHEDULE_NAME}"
        response = client.delete(
            url,
            headers=headers,
        )
        assert response.status_code == 204
        url = f"/tasks/{task}"
        response = client.get(
            url,
            headers=headers,
        )
        assert response.status_code == 200
        assert "schedule_name" in response.json
        assert response.json["schedule_name"] is None
        assert "original_schedule_name" in response.json
        assert response.json["original_schedule_name"] == SCHEDULE_NAME
