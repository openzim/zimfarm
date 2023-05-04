import pytest

from common.external import build_workers_whitelist


class TestWorkersCommon:
    def test_build_workers_whitelist(self, workers):
        whitelist = build_workers_whitelist()
        assert len(whitelist) == 36


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
        assert response_json["meta"]["count"] == 38

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
    def test_checkin_existing_worker(self, client, access_token, worker):
        url = f"/workers/{worker['name']}/check-in"
        payload = {
            "username": worker["username"],
            "cpu": 4,
            "memory": 2048,
            "disk": 4096,
            "offliners": ["mwoffliner", "phet"],
        }
        response = client.put(
            url, json=payload, headers={"Authorization": access_token}
        )
        assert response.status_code == 204

    def test_checkin_new_worker(self, client, access_token, user, cleanup_create_test):
        url = "/workers/some_worker_create_test/check-in"
        payload = {
            "username": user["username"],
            "cpu": 4,
            "memory": 2048,
            "disk": 4096,
            "offliners": ["mwoffliner", "phet"],
        }
        response = client.put(
            url, json=payload, headers={"Authorization": access_token}
        )
        assert response.status_code == 204

    @pytest.mark.parametrize(
        "payload, error_msg",
        [
            (
                {  # missing username
                    "cpu": 4,
                    "memory": 2048,
                    "disk": 4096,
                    "offliners": ["mwoffliner", "phet"],
                },
                "Invalid Request JSON",
            ),
            (
                {  # username not present in DB
                    "username": "bob",
                    "cpu": 4,
                    "memory": 2048,
                    "disk": 4096,
                    "offliners": ["mwoffliner", "phet"],
                },
                "username not found",
            ),
            (
                {  # invalid CPU value
                    "username": "some-user",
                    "cpu": -1,
                    "memory": 2048,
                    "disk": 4096,
                    "offliners": ["mwoffliner", "phet"],
                },
                "Invalid Request JSON",
            ),
            (
                {  # invalid offliner value
                    "username": "some-user",
                    "cpu": 4,
                    "memory": 2048,
                    "disk": 4096,
                    "offliners": ["mwoffliner", "phet", "pouet"],
                },
                "Invalid Request JSON",
            ),
        ],
    )
    def test_bad_checkin(self, client, access_token, worker, payload, error_msg):
        url = f"/workers/{worker['name']}/check-in"
        response = client.put(
            url, json=payload, headers={"Authorization": access_token}
        )
        assert response.status_code == 400
        assert response.get_json()["error"] == error_msg

    def test_checkin_deleted_worker(self, client, access_token, workers):
        url = "/workers/deleted_worker/check-in"
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
        assert response.status_code == 400
        assert response.get_json()["error"] == "worker has been marked as deleted"

    def test_checkin_deleted_user(self, client, access_token, workers, deleted_user):
        url = "/workers/worker_from_deleted_user/check-in"
        payload = {
            "username": deleted_user["username"],
            "cpu": 4,
            "memory": 2048,
            "disk": 4096,
            "offliners": ["mwoffliner", "phet"],
        }
        response = client.put(
            url, json=payload, headers={"Authorization": access_token}
        )
        assert response.status_code == 400
        assert response.get_json()["error"] == "username not found"

    def test_checkin_user_does_not_exists(self, client, access_token, worker):
        url = f"/workers/{worker['name']}/check-in"
        payload = {
            "username": "idontexists",
            "cpu": 4,
            "memory": 2048,
            "disk": 4096,
            "offliners": ["mwoffliner", "phet"],
        }
        response = client.put(
            url, json=payload, headers={"Authorization": access_token}
        )
        assert response.status_code == 400
        assert response.get_json()["error"] == "username not found"

    def test_checkin_another_user(
        self, client, access_token, worker, workers, deleted_user
    ):
        url = f"/workers/{workers[10]}/check-in"
        payload = {
            "username": "user_1",
            "cpu": 4,
            "memory": 2048,
            "disk": 4096,
            "offliners": ["mwoffliner", "phet"],
        }
        response = client.put(
            url, json=payload, headers={"Authorization": access_token}
        )
        # for now we accept that a worker changes its associated user
        assert response.status_code == 204
        # assert (
        #     response.get_json()["error"]
        #     == "worker with same name already exists for another user"
        # )
