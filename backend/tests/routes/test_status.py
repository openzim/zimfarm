import time
from collections.abc import Callable
from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient

from zimfarm_backend.common.enums import TaskStatus
from zimfarm_backend.db.models import Task


@pytest.mark.parametrize(
    "query,expected_reponse",
    [
        pytest.param(
            "oldest_task_older_than?status=scraper_started&threshold_secs=500",
            "oldest_task_older_than for scraper_started and 500s: OK",
            id="oldest_task_older_than_ok",
        ),
        pytest.param(
            "oldest_task_older_than?status=scraper_started&threshold_secs=1",
            "oldest_task_older_than for scraper_started and 1s: KO",
            id="oldest_task_older_than_ko",
        ),
    ],
)
def test_status_get(
    client: TestClient,
    create_task: Callable[..., Task],
    query: str,
    expected_reponse: str,
):
    for _ in range(5):
        create_task(status=TaskStatus.requested)
        create_task(status=TaskStatus.reserved)
        create_task(status=TaskStatus.started)
        create_task(status=TaskStatus.scraper_started)
        create_task(status=TaskStatus.succeeded)
        create_task(status=TaskStatus.failed)

    # needed to ensure that the task is older than 1 second
    time.sleep(1)
    response = client.get(f"/v2/status/{query}")
    assert response.status_code == HTTPStatus.OK
    assert response.text == expected_reponse
