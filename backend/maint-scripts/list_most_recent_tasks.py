import sys
from typing import Any

import requests

from get_token import get_token, get_token_headers, get_url
from zimfarm_backend.common.constants import REQUESTS_TIMEOUT


def get_timestamp(task: dict[str, Any], status: str) -> str:
    if status in task["timestamp"]:
        return task["timestamp"][status]
    else:
        return "-"


def main(username: str, password: str):
    """Print in STDOUT a markdown table of recipe most recent tasks"""
    access_token, _ = get_token(username, password)
    response = requests.get(
        url=get_url("/recipes/?limit=20&name=wikihow"),
        headers=get_token_headers(access_token),
        timeout=REQUESTS_TIMEOUT,
    )
    recipes = response.json()["items"]
    print(  # noqa: T201
        "| Recipe name | Task ID | status | started | scraper_completed |"
    )
    print("|--|--|--|--|--|")  # noqa: T201

    datas: list[dict[str, Any]] = []
    for recipe in sorted(recipes, key=lambda recipe: recipe["name"]):
        response = requests.get(
            f"{get_url('/tasks')}/{recipe['most_recent_task']['_id']}",
            headers=get_token_headers(access_token),
            timeout=REQUESTS_TIMEOUT,
        )
        most_recent_task = response.json()

        datas.append(
            {
                "recipe": recipe,
                "most_recent_task": most_recent_task,
                "scraper_completed": get_timestamp(
                    most_recent_task, "scraper_completed"
                ),
            }
        )

    for data in sorted(datas, key=lambda data: data["scraper_completed"]):
        recipe = data["recipe"]
        most_recent_task = data["most_recent_task"]
        print(  # noqa: T201
            f"| [{recipe['name']}]"
            f"(https://farm.openzim.org/recipes/{recipe['name']}) "
            f"| [{most_recent_task['_id']}]"
            f"(https://farm.openzim.org/pipeline/{most_recent_task['_id']}) "
            f"| {most_recent_task['status']} "
            f"| {get_timestamp(most_recent_task, 'started')[:19]} "
            f"| {get_timestamp(most_recent_task, 'scraper_completed')[:19]} "
            f"|"
        )


if __name__ == "__main__":
    args = sys.argv[1:]
    main(*args)
