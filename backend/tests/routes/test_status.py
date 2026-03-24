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
        create_task(status=TaskStatus.requested, recipe_name="recipe_1")
        create_task(status=TaskStatus.reserved, recipe_name="recipe_2")
        create_task(status=TaskStatus.started, recipe_name="recipe_3")
        create_task(status=TaskStatus.scraper_started, recipe_name="recipe_4")
        create_task(status=TaskStatus.succeeded, recipe_name="recipe_5")
        create_task(status=TaskStatus.failed, recipe_name="recipe_6")

    # needed to ensure that the task is older than 1 second
    time.sleep(1)
    response = client.get(f"/v2/status/{query}")
    assert response.status_code == HTTPStatus.OK
    assert response.text == expected_reponse
