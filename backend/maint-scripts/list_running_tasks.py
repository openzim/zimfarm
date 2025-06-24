import sys
from typing import Any

import requests
from get_token import get_token, get_token_headers, get_url

from zimfarm_backend.common.constants import REQUESTS_TIMEOUT

running_statuses = [
    "reserved",
    "started",
    "scraper_started",
    "scraper_completed",
    "scraper_killed",
    "cancel_requested",
]


def get_status_query():
    filters = [f"status={status}" for status in running_statuses]
    return "&".join(filters)


def get_timestamp(task: dict[str, Any], status: str) -> str:
    if status in task["timestamp"]:
        return task["timestamp"][status]
    else:
        return "-"


def main(username: str, password: str):
    """Print in STDOUT a markdown table of running tasks with various information"""
    access_token, _ = get_token(username, password)
    response = requests.get(
        f"{get_url('/tasks')}?{get_status_query()}",
        headers=get_token_headers(access_token),
        timeout=REQUESTS_TIMEOUT,
    )
    tasks = response.json()["items"]
    print(  # noqa: T201
        "| Task ID | worker | kind | DB Status | last update at | requested"
        " | reserved | started | scraper_started | scraper_completed |"
    )
    print("|--|--|--|--|--|--|--|--|--|--|")  # noqa: T201
    for task in sorted(tasks, key=lambda task: task["updated_at"]):
        response = requests.get(
            f"{get_url('/tasks')}/{task['_id']}",
            headers=get_token_headers(access_token),
            timeout=REQUESTS_TIMEOUT,
        )
        task_details = response.json()

        print(  # noqa: T201
            f"| [{task['_id']}](https://farm.openzim.org/pipeline/{task['_id']}) "
            f"| {task['worker']} "
            f"| {task_details['config']['task_name']} "
            f"| {task['status']} "
            f"| {task['updated_at'][:19]} "
            f"| {get_timestamp(task, 'requested')[:19]} "
            f"| {get_timestamp(task, 'reserved')[:19]} "
            f"| {get_timestamp(task, 'started')[:19]} "
            f"| {get_timestamp(task, 'scraper_started')[:19]} "
            f"| {get_timestamp(task, 'scraper_completed')[:19]} "
            f"|"
        )


if __name__ == "__main__":
    args = sys.argv[1:]
    main(*args)
