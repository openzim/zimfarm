from pathlib import Path
from typing import Any

import requests
import json

from recipesauto.context import Context
from recipesauto.utils import check_zim_name, get_language_data

context = Context.get()

IGNORED_DOMAINS = []


def get_recipe_tag() -> str:
    return "stack-exchange"


def get_expected_recipes() -> list[dict[str, Any]]:

    resp = requests.get(
        "http://org-kiwix-stackexchange.s3.us-west-1.wasabisys.com/summary.json",
        allow_redirects=True,
        timeout=context.http_timeout,
    )
    resp.raise_for_status()

    archives = json.loads(resp.text)["archives"]

    del resp

    def get_language_code(archive: str):
        if archive in ["ru.stackoverflow.com", "rus.stackexchange.com"]:
            return "ru"
        elif archive == "pt.stackoverflow.com":
            return "pt"
        elif archive == "es.stackoverflow.com":
            return "es"
        elif archive == "ja.stackoverflow.com":
            return "ja"
        elif archive in [
            "russian.stackexchange.com",
            "chinese.stackexchange.com",
            "esperanto.stackexchange.com",
            "french.stackexchange.com",
            "italian.stackexchange.com",
            "ja.stackoverflow.com",
            "japanese.stackexchange.com",
            "korean.stackexchange.com",
            "latin.stackexchange.com",
            "portuguese.stackexchange.com",
            "spanish.stackexchange.com",
            "ukrainian.stackexchange.com",
        ]:
            return "mul"
        return "en"

    def get_mapped_name(archive: str):
        map_data = {"beer.stackexchange.com": "alcohol.stackexchange.com"}
        return map_data.get(archive, archive)

    def get_name(archive: str):
        return f"{get_mapped_name(archive)}_{get_language_code(archive)}"

    config_data = json.loads((Path(__file__).parent / "stackexchange.json").read_text())

    return [
        {
            "category": "stack_exchange",
            "config": {
                "flags": {
                    "optimization-cache": context.values["stackexchange_optim_url"],
                    "mirror": "https://org-kiwix-stackexchange.s3.us-west-1.wasabisys.com",
                    "publisher": "openZIM",
                    "threads": "8",
                    "domain": archive,
                    "stats-filename": "/output/task_progress.json",
                    "output": "/output",
                    "redis-url": "unix:///var/run/redis.sock",
                    "keep-redis": True,
                    "title": config_data[get_name(archive)]["title"],
                    "description": config_data[get_name(archive)]["description"],
                },
                "monitor": False,
                "platform": None,
                "image": {"name": "ghcr.io/openzim/sotoki", "tag": "2.2.1"},
                "resources": config_data[get_name(archive)]["resources"],
                "task_name": "sotoki",
                "warehouse_path": "/stack_exchange",
            },
            "enabled": True,
            "language": get_language_data(get_language_code(archive)),
            "name": get_name(archive),
            "periodicity": "biannualy",
            "tags": ["stack-exchange"],
        }
        for archive in archives
        if archive not in IGNORED_DOMAINS
    ]
