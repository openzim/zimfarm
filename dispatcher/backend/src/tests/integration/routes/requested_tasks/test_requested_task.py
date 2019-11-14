import json

from bson import ObjectId
import pytest


class TestRequestedTaskList:
    url = "/requested-tasks/"

    def _assert_requested_task(self, task, item):
        assert set(item.keys()) == {
            "_id",
            "status",
            "schedule_id",
            "schedule_name",
            "timestamp",
            "config",
        }
        assert item["_id"] == str(task["_id"])
        assert item["status"] == task["status"]
        assert item["schedule_id"] == str(task["schedule_id"])
        assert item["schedule_name"] == task["schedule_name"]

    @pytest.mark.parametrize(
        "query_param", [{"schedule_id": "a"}, {"schedule_id": 123}]
    )
    def test_bad_rquest(self, client, query_param):
        headers = {"Content-Type": "application/json"}
        response = client.get(self.url, headers=headers, query_string=query_param)
        assert response.status_code == 400

    def test_list(self, client, requested_tasks):

        headers = {"Content-Type": "application/json"}
        response = client.get(self.url, headers=headers)
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["meta"]["limit"] == 100
        assert data["meta"]["skip"] == 0

        items = data["items"]
        requested_tasks.sort(key=lambda task: task["_id"], reverse=True)
        assert len(items) == len(requested_tasks)
        for index, task in enumerate(requested_tasks):
            item = items[index]
            self._assert_requested_task(task, item)

    def test_list_pagination(self, client, requested_tasks):
        url = "/requested-tasks/?limit={}&skip={}".format(10, 5)
        headers = {"Content-Type": "application/json"}
        response = client.get(url, headers=headers)
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["meta"]["limit"] == 10
        assert data["meta"]["skip"] == 5


class TestRequestedTaskGet:
    def test_not_found(self, client):
        url = "/requested-tasks/task_id"
        headers = {"Content-Type": "application/json"}
        response = client.get(url, headers=headers)
        assert response.status_code == 404

    def test_get(self, client, requested_task):
        url = "/requested-tasks/{}".format(requested_task["_id"])
        headers = {"Content-Type": "application/json"}
        response = client.get(url, headers=headers)
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["_id"] == str(requested_task["_id"])
        assert data["status"] == requested_task["status"]
        assert data["schedule_id"] == str(requested_task["schedule_id"])
        assert data["schedule_name"] == requested_task["schedule_name"]
        assert "timestamp" in data
        assert "events" in data


class TestRequestedTaskCreate:
    @pytest.fixture()
    def requested_task(self, make_requested_task):
        requested_task = make_requested_task()
        return requested_task

    def test_create_from_schedule(self, database, client, access_token, schedule):
        url = "/requested-tasks/"
        headers = {"Authorization": access_token, "Content-Type": "application/json"}
        response = client.post(
            url,
            headers=headers,
            data=json.dumps({"schedule_names": [schedule["name"]]}),
        )
        assert response.status_code == 201

        data = json.loads(response.data)
        database.requested_tasks.delete_one(
            {"_id": ObjectId(data["requested"][0]["_id"])}
        )

    def test_create_with_wrong_schedule(self, client, access_token, schedule):
        url = "/requested-tasks/"
        headers = {"Authorization": access_token, "Content-Type": "application/json"}
        response = client.post(
            url, headers=headers, data=json.dumps({"schedule_names": ["hello"]})
        )
        assert response.status_code == 404
