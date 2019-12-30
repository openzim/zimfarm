import json

import pytest
from bson import ObjectId

from common.enum import TaskStatus


def _find_match(sequence, column, item):
    return list(
        filter(lambda sq_item: str(sq_item[column]) == str(item[column]), sequence)
    ).pop()


def _find_matches(sequencea, sequenceb, column):
    return [(item, _find_match(sequenceb, "_id", item)) for item in sequencea]


class TestTaskCreate:
    @pytest.fixture()
    def requested_task(self, make_requested_task):
        requested_task = make_requested_task()
        return requested_task

    def test_create_from_schedule(self, database, client, access_token, requested_task):
        url = "/tasks/{}".format(str(requested_task["_id"]))
        headers = {"Authorization": access_token, "Content-Type": "application/json"}
        response = client.post(
            url, headers=headers, query_string={"worker_name": "zimfarm_worker.com"}
        )
        assert response.status_code == 201

        data = json.loads(response.data)
        database.tasks.delete_one({"_id": ObjectId(data["_id"])})

    def test_create_with_missing_worker(self, client, access_token, requested_task):
        url = "/tasks/{}".format(str(requested_task["_id"]))
        response = client.post(url, headers={"Authorization": access_token})
        assert response.status_code == 400


class TestTaskList:
    url = "/tasks/"

    def _assert_task(self, task, item):
        assert set(item.keys()) == {
            "_id",
            "timestamp",
            "status",
            "schedule_name",
            "worker",
            "updated_at",
        }
        assert item["_id"] == str(task["_id"])
        assert item["status"] == task["status"]

    @pytest.mark.parametrize("query_param", [{"schedule_id": "a"}, {"status": 123}])
    def test_bad_request(self, client, query_param):
        headers = {"Content-Type": "application/json"}
        response = client.get(self.url, headers=headers, query_string=query_param)
        assert response.status_code == 400

    def test_list(self, client, tasks):
        headers = {"Content-Type": "application/json"}
        response = client.get(self.url, headers=headers)
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["meta"]["limit"] == 20
        assert data["meta"]["skip"] == 0

        items = data["items"]
        assert len(items) == data["meta"]["limit"]
        matches = _find_matches(items, tasks, "_id")
        assert len(items) == len(matches)
        for m_item, m_task in matches:
            self._assert_task(m_task, m_item)

    def test_list_pagination(self, client, tasks):
        url = "/tasks/?limit={}&skip={}".format(10, 5)
        headers = {"Content-Type": "application/json"}
        response = client.get(url, headers=headers)
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["meta"]["limit"] == 10
        assert data["meta"]["skip"] == 5

    @pytest.mark.parametrize(
        "statuses", [[TaskStatus.succeeded], [TaskStatus.succeeded, TaskStatus.started]]
    )
    def test_status(self, client, tasks, statuses):
        url = f"/tasks/?"
        for status in statuses:
            url += f"status={status}&"

        headers = {"Content-Type": "application/json"}
        response = client.get(url, headers=headers)
        assert response.status_code == 200

        tasks = {task["_id"]: task for task in tasks if task["status"] in statuses}
        items = json.loads(response.data)["items"]

        assert len(tasks) == len(items)
        for item in items:
            task = tasks[ObjectId(item["_id"])]
            self._assert_task(task, item)

    def test_schedule_name(self, client, make_task):
        """Test list tasks with schedule_name as filter"""

        # generate tasks with two schedule ids
        schedule_name, another_schedule_name = str(ObjectId()), str(ObjectId())
        for _ in range(5):
            make_task(schedule_name=schedule_name)
        for _ in range(10):
            make_task(schedule_name=another_schedule_name)

        # make request
        headers = {"Content-Type": "application/json"}
        response = client.get(
            self.url, headers=headers, query_string={"schedule_name": schedule_name}
        )
        assert response.status_code == 200

        # check the correct number of schedule is returned
        items = json.loads(response.data)["items"]
        assert len(items) == 5


class TestTaskGet:
    def test_not_found(self, client):
        url = "/tasks/task_id"
        headers = {"Content-Type": "application/json"}
        response = client.get(url, headers=headers)
        assert response.status_code == 404

    def test_get(self, client, task):
        url = "/tasks/{}".format(task["_id"])
        headers = {"Content-Type": "application/json"}
        response = client.get(url, headers=headers)
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["_id"] == str(task["_id"])
        assert data["status"] == task["status"]
        assert data["schedule_name"] == task["schedule_name"]
        assert "timestamp" in data
        assert "events" in data


class TestTaskCancel:
    def test_unauthorized(self, client, task):
        url = "/tasks/{}/cancel".format(task["_id"])
        response = client.post(url)
        assert response.status_code == 401

    def test_not_found(self, client, access_token):
        url = "/tasks/task_id/cancel"
        headers = {"Authorization": access_token, "Content-Type": "application/json"}
        response = client.post(url, headers=headers)
        assert response.status_code == 404

    def test_wrong_statuses(self, client, access_token, tasks):
        for task in filter(lambda x: x["status"] not in TaskStatus.incomplete(), tasks):
            url = "/tasks/{}/cancel".format(task["_id"])
            headers = {
                "Authorization": access_token,
                "Content-Type": "application/json",
            }
            response = client.post(url, headers=headers)
            assert response.status_code == 404

    def test_cancel_task(self, client, access_token, tasks):
        for task in filter(lambda x: x["status"] in TaskStatus.incomplete(), tasks):
            url = "/tasks/{}/cancel".format(task["_id"])
            headers = {
                "Authorization": access_token,
                "Content-Type": "application/json",
            }
            response = client.post(url, headers=headers)
            assert response.status_code == 204
