from typing import Any, Dict, List

import pytest

import db.models as dbm
from common import constants
from common.external import ExternalIpUpdater, build_workers_whitelist


class TestWorkersCommon:
    def test_build_workers_whitelist(self, workers, dbsession):
        whitelist = build_workers_whitelist(session=dbsession)
        # - 4 because:
        # 2 workers have a duplicate IP
        # 1 worker has an IP missing
        # 1 worker is marked as deleted
        # 1 worker has its user marked as deleted
        assert len(whitelist) == len(workers) - 4


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


class TestWorkerRequestedTasks:
    @pytest.fixture()
    def req_task_query_string(self, worker):
        return {
            "worker": worker["name"],
            "avail_cpu": 4,
            "avail_memory": 2048,
            "avail_disk": 4096,
        }

    @pytest.fixture
    def make_headers(self):
        def _make_headers(access_token: str, client_ip: str) -> Dict[str, Any]:
            return {
                "Authorization": access_token,
                "X-Forwarded-For": client_ip,
            }

        return _make_headers

    @pytest.fixture
    def admin_headers(self, make_headers, access_token, default_ip):
        def _admin_headers(
            access_token: str = access_token, client_ip: str = default_ip
        ) -> Dict[str, Any]:
            return make_headers(access_token=access_token, client_ip=client_ip)

        return _admin_headers

    @pytest.fixture
    def worker_headers(self, make_headers, make_access_token, worker, default_ip):
        def _worker_headers(
            access_token: str = make_access_token(worker["username"], "worker"),
            client_ip: str = default_ip,
        ) -> Dict[str, Any]:
            return make_headers(access_token=access_token, client_ip=client_ip)

        return _worker_headers

    @pytest.fixture
    def default_ip(self):
        return "192.168.1.1"

    @pytest.fixture
    def increase_ip(self):
        def _increase_ip(prev_ip):
            return f"{str(prev_ip)[:-1]}{int(str(prev_ip)[-1])+1}"

        return _increase_ip

    def test_requested_task_worker_as_admin(
        self,
        client,
        worker,
        req_task_query_string,
        admin_headers,
        dbsession,
        increase_ip,
    ):
        # Retrieve current object from DB
        db_worker = dbm.Worker.get(dbsession, worker["name"])
        last_seen = db_worker.last_seen
        last_ip = db_worker.last_ip

        response = client.get(
            "/requested-tasks/worker",
            query_string=req_task_query_string,
            headers=admin_headers(client_ip=increase_ip(last_ip)),
        )
        assert response.status_code == 200

        # Refresh current object from DB
        dbsession.expire(db_worker)
        db_worker = dbm.Worker.get(dbsession, worker["name"])
        # last_seen and last_ip are not updated when endpoint is called as admin
        assert last_seen == db_worker.last_seen
        assert last_ip == db_worker.last_ip

    def test_requested_task_worker_as_worker(
        self,
        client,
        worker,
        worker_headers,
        req_task_query_string,
        increase_ip,
        dbsession,
    ):
        # Retrieve current object from DB
        db_worker = dbm.Worker.get(dbsession, worker["name"])
        last_seen = db_worker.last_seen
        last_ip = db_worker.last_ip
        new_ip = increase_ip(last_ip)
        # Worker checks for requested tasks
        response = client.get(
            "/requested-tasks/worker",
            query_string=req_task_query_string,
            headers=worker_headers(client_ip=new_ip),
        )
        assert response.status_code == 200

        # Refresh current object from DB
        dbsession.expire(db_worker)
        db_worker = dbm.Worker.get(dbsession, worker["name"])
        # last_seen and last_ip are updated in DB when endpoint is called as worker
        assert last_seen != db_worker.last_seen
        assert last_ip != db_worker.last_ip
        assert str(db_worker.last_ip) == new_ip

        # second call will update only the last_seen attribute
        last_seen = db_worker.last_seen
        last_ip = db_worker.last_ip
        response = client.get(
            "/requested-tasks/worker",
            query_string=req_task_query_string,
            headers=worker_headers(client_ip=new_ip),
        )
        assert response.status_code == 200

        # Refresh current object from DB again
        dbsession.expire(db_worker)
        db_worker = dbm.Worker.get(dbsession, worker["name"])
        # last_seen has been updated again but not last_ip which did not changed
        assert last_seen != db_worker.last_seen
        assert str(db_worker.last_ip) == new_ip

    @pytest.mark.parametrize(
        "prev_ip, new_ip, external_update_enabled, external_update_fails,"
        " external_update_called",
        [
            ("77.77.77.77", "88.88.88.88", False, False, False),  # ip update disabled
            ("77.77.77.77", "77.77.77.77", True, False, False),  # ip did not changed
            ("77.77.77.77", "88.88.88.88", True, False, True),  # ip should be updated
            ("77.77.77.77", "88.88.88.88", True, True, False),  # ip update fails
        ],
    )
    def test_requested_task_worker_update_ip_whitelist(
        self,
        client,
        worker,
        req_task_query_string,
        prev_ip,
        new_ip,
        worker_headers,
        external_update_enabled,
        external_update_fails,
        external_update_called,
    ):
        # call it once to set prev_ip
        response = client.get(
            "/requested-tasks/worker",
            query_string=req_task_query_string,
            headers=worker_headers(client_ip=prev_ip),
        )
        assert response.status_code == 200

        # check prev_ip has been set
        response = client.get("/workers/")
        assert response.status_code == 200
        response_data = response.get_json()
        for item in response_data["items"]:
            if item["name"] != worker["name"]:
                continue
            assert item["last_ip"] == prev_ip

        # setup custom ip updater to intercept Wasabi operations
        updater = IpUpdaterAndChecker(should_fail=external_update_fails)
        assert new_ip not in updater.ip_addresses
        ExternalIpUpdater.update = updater.ip_update
        constants.USES_WORKERS_IPS_WHITELIST = external_update_enabled

        # call it once to set next_ip
        response = client.get(
            "/requested-tasks/worker",
            query_string=req_task_query_string,
            headers=worker_headers(client_ip=new_ip),
        )
        if external_update_fails:
            assert response.status_code == 503
        else:
            assert response.status_code == 200
            assert updater.ips_updated == external_update_called
            if external_update_called:
                assert new_ip in updater.ip_addresses

        # check new_ip has been set (even if ip update is disabled or has failed)
        response = client.get("/workers/")
        assert response.status_code == 200
        response_data = response.get_json()
        for item in response_data["items"]:
            if item["name"] != worker["name"]:
                continue
            assert item["last_ip"] == new_ip


class IpUpdaterAndChecker:
    """Helper class to intercept Wasabi operations and perform assertions"""

    def __init__(self, should_fail: bool) -> None:
        self.ips_updated = False
        self.should_fail = should_fail
        self.ip_addresses = []

    def ip_update(self, ip_addresses: List):
        if self.should_fail:
            raise Exception()
        else:
            self.ips_updated = True
            self.ip_addresses = ip_addresses
