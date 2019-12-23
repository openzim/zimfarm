import json

from bson import ObjectId
import pytest


class TestRequestedTaskList:
    url = "/requested-tasks/"

    def _assert_requested_task(self, task, item):
        assert set(item.keys()) == {
            "_id",
            "status",
            "schedule_name",
            "timestamp",
            "config",
            "requested_by",
            "priority",
        }
        assert item["_id"] == str(task["_id"])
        assert item["status"] == task["status"]
        assert item["schedule_name"] == task["schedule_name"]

    @pytest.mark.parametrize(
        "query_param", [{"matching_cpu": "-2"}, {"matching_memory": -1}]
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
        assert data["meta"]["limit"] == 20
        assert data["meta"]["skip"] == 0

        items = data["items"]
        # items ordering is done by mongo and not important to us
        # but we need to match our requests with result to test resulting data
        sorted_requested_tasks = list(
            map(
                lambda item: [
                    r for r in requested_tasks if str(r["_id"]) == item["_id"]
                ][-1],
                items,
            )
        )
        assert len(items) == len(sorted_requested_tasks)
        # assert sorting
        assert str(sorted_requested_tasks[0]["_id"]) == items[0]["_id"]
        for index, task in enumerate(sorted_requested_tasks):
            item = items[index]
            self._assert_requested_task(task, item)

    @pytest.mark.parametrize(
        "matching, expected",
        [
            [{"cpu": 3, "memory": 1024, "disk": 1024}, 20],
            [
                {
                    "cpu": 3,
                    "memory": 1024,
                    "disk": 1024,
                    "offliners": ["mwoffliner", "phet", "gutenberg", "youtube"],
                },
                20,
            ],
            [
                {
                    "cpu": 2,
                    "memory": 1024,
                    "disk": 1024,
                    "offliners": ["mwoffliner", "phet", "gutenberg", "youtube"],
                },
                0,
            ],
            [
                {
                    "cpu": 3,
                    "memory": 1023,
                    "disk": 1024,
                    "offliners": ["mwoffliner", "phet", "gutenberg", "youtube"],
                },
                0,
            ],
            [
                {
                    "cpu": 3,
                    "memory": 1024,
                    "disk": 1023,
                    "offliners": ["mwoffliner", "phet", "gutenberg", "youtube"],
                },
                0,
            ],
            [
                {
                    "cpu": 3,
                    "memory": 1024,
                    "disk": 1024,
                    "offliners": ["mwoffliner", "phet", "gutenberg"],
                },
                0,
            ],
        ],
    )
    def test_list_matching(self, client, requested_tasks, matching, expected):

        url = f"{self.url}?"
        for key, value in matching.items():
            if isinstance(value, list):
                for lvalue in value:
                    url += f"matching_{key}={lvalue}&"
            else:
                url += f"matching_{key}={value}&"
        headers = {"Content-Type": "application/json"}
        response = client.get(url, headers=headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        items = data["items"]
        assert len(items) == expected

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
        database.requested_tasks.delete_one({"_id": ObjectId(data["requested"][0])})

    def test_create_with_wrong_schedule(self, client, access_token, schedule):
        url = "/requested-tasks/"
        headers = {"Authorization": access_token, "Content-Type": "application/json"}
        response = client.post(
            url, headers=headers, data=json.dumps({"schedule_names": ["hello"]})
        )
        assert response.status_code == 404
