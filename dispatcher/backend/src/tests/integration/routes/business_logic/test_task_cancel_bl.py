import json

import pytest

import db.models as dbm
from db import Session

SCHEDULE_NAME = "a_schedule_for_tasks"


class TestTaskBusiness:
    @pytest.fixture(scope="module")
    def headers(self, access_token):
        return {"Authorization": access_token, "Content-Type": "application/json"}

    @pytest.fixture()
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

    def test_task_cancel_requested(self, client, headers, username, task):
        url = f"/tasks/{task}"

        def get_task():
            response = client.get(
                url,
                headers=headers,
            )
            assert response.status_code == 200
            return response

        def patch_to_status(status, payload={}):
            response = client.patch(
                url,
                headers=headers,
                data=json.dumps({"event": status, "payload": payload}),
            )
            assert response.status_code == 204

        response = get_task()
        assert "canceled_by" in response.json
        assert response.json["canceled_by"] is None

        patch_to_status("started")
        response = get_task()
        assert "canceled_by" in response.json
        assert response.json["canceled_by"] is None

        patch_to_status("scraper_started")
        response = get_task()
        assert "canceled_by" in response.json
        assert response.json["canceled_by"] is None

        response = client.post(
            f"{url}/cancel",
            headers=headers,
        )
        assert response.status_code == 204
        response = get_task()
        assert "status" in response.json
        assert response.json["status"] == "cancel_requested"
        assert "canceled_by" in response.json
        assert response.json["canceled_by"] == username

        patch_to_status("canceled", payload={"canceled_by": "bob"})
        response = get_task()
        assert "canceled_by" in response.json
        assert response.json["canceled_by"] == username

    def test_task_cancel_in_db(self, client, headers, username, task):
        url = f"/tasks/{task}"

        def get_task():
            response = client.get(
                url,
                headers=headers,
            )
            assert response.status_code == 200
            return response

        def patch_to_status(status, payload={}):
            response = client.patch(
                url,
                headers=headers,
                data=json.dumps({"event": status, "payload": payload}),
            )
            assert response.status_code == 204

        response = get_task()
        assert "canceled_by" in response.json
        assert response.json["canceled_by"] is None

        patch_to_status("started")
        response = get_task()
        assert "canceled_by" in response.json
        assert response.json["canceled_by"] is None

        patch_to_status("scraper_started")
        response = get_task()
        assert "canceled_by" in response.json
        assert response.json["canceled_by"] is None

        with Session.begin() as session:
            task = dbm.Task.get(session, task)
            task.status = "cancel_requested"

        response = get_task()
        assert "canceled_by" in response.json
        assert response.json["canceled_by"] is None
        assert "status" in response.json
        assert response.json["status"] == "cancel_requested"

        CANCELED_BY = "bob"
        patch_to_status("canceled", payload={"canceled_by": CANCELED_BY})
        response = get_task()
        assert "canceled_by" in response.json
        assert response.json["canceled_by"] == CANCELED_BY
