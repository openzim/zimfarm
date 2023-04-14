import pytest

from common.external import build_workers_whitelist


class TestWorkersCommon:
    def test_build_workers_whitelist(self, workers):
        whitelist = build_workers_whitelist()
        assert len(whitelist) == len(workers)


class TestWorkersList:
    def test_list_workers_no_param(self, client, workers):
        """Test workers list"""

        url = "/workers/"
        response = client.get(url)
        assert response.status_code == 200

        response_json = response.get_json()
        assert "items" in response_json
        assert len(response_json["items"]) == 20
        for item in response_json["items"]:
            assert set(item.keys()) == {
                "username",
                "name",
                "offliners",
                "resources",
                "last_seen",
                "last_ip",
                "status",
            }

    @pytest.mark.parametrize(
        "skip, limit, expected", [(0, 1, 1), (1, 10, 10), (0, 100, 38)]
    )
    def test_list_workers_with_param(self, client, workers, skip, limit, expected):
        """Test workers list with skip and limit"""

        url = "/workers/?skip={}&limit={}".format(skip, limit)
        response = client.get(url)
        assert response.status_code == 200

        response_json = response.get_json()
        assert "items" in response_json
        assert len(response_json["items"]) == expected

    @pytest.mark.parametrize("skip, limit", [("", 10), (5, "abc")])
    def test_list_workers_bad_param(self, client, schedules, skip, limit):
        """Test workers list with bad skip and limit"""

        url = "/workers/?skip={}&limit={}".format(skip, limit)
        response = client.get(url)
        assert response.status_code == 400


class TestWorkerCheckIn:
    name = "myworker"

    def test_checkin(self, database, client, access_token, worker):
        url = f"/workers/{self.name}/check-in"
        payload = {
            "username": "some-user",
            "cpu": 4,
            "memory": 2048,
            "disk": 4096,
            "offliners": ["mwoffliner", "phet"],
        }
        response = client.put(
            url, json=payload, headers={"Authorization": access_token}
        )
        assert response.status_code == 204
        database.workers.delete_one({"username": payload["username"]})

    @pytest.mark.parametrize(
        "payload",
        [
            {  # missing username
                "cpu": 4,
                "memory": 2048,
                "disk": 4096,
                "offliners": ["mwoffliner", "phet"],
            },
            {  # username not present in DB
                "username": "bob",
                "cpu": 4,
                "memory": 2048,
                "disk": 4096,
                "offliners": ["mwoffliner", "phet"],
            },
            {  # invalid CPU value
                "username": "some-user",
                "cpu": -1,
                "memory": 2048,
                "disk": 4096,
                "offliners": ["mwoffliner", "phet"],
            },
            {  # invalid offliner value
                "username": "some-user",
                "cpu": 4,
                "memory": 2048,
                "disk": 4096,
                "offliners": ["mwoffliner", "phet", "pouet"],
            },
        ],
    )
    def test_bad_checkin(self, database, client, access_token, worker, payload):
        url = f"/workers/{self.name}/check-in"
        response = client.put(
            url, json=payload, headers={"Authorization": access_token}
        )
        assert response.status_code == 400
        database.workers.delete_one({"name": self.name})
