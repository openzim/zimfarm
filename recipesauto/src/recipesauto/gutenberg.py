from typing import Any

import requests
from bs4 import BeautifulSoup, Tag

from recipesauto.context import Context
from recipesauto.utils import check_zim_name, get_language_data

context = Context.get()


def get_recipe_tag() -> str:
    return "gutenberg"


def get_expected_recipes() -> list[dict[str, Any]]:

    resp = requests.get(
        "https://www.gutenberg.org/ebooks/",
        allow_redirects=True,
        timeout=context.http_timeout,
    )
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "lxml")

    select_tag = soup.find("select", id="lang")

    if not isinstance(select_tag, Tag):
        raise Exception("Bad HTML document")

    lang_codes = [
        option["value"]
        for option in select_tag.find_all("option")
        if option.get("value")  # skips empty string or missing value
    ]

    del resp
    del soup
    del select_tag

    return [
        {
            "category": "gutenberg",
            "config": {
                "flags": {
                    "bookshelves": True,
                    "languages": lang_code,
                    "optimization-cache": context.values["gutenberg_optim_url"],
                    "publisher": "openZIM",
                },
                "monitor": False,
                "platform": "gutenberg",
                "image": {"name": "ghcr.io/openzim/gutenberg", "tag": "2.2.0"},
                "resources": {"cpu": 3, "disk": 322122547200, "memory": 16106127360},
                "task_name": "gutenberg",
                "warehouse_path": "/gutenberg",
            },
            "enabled": True,
            "language": get_language_data(lang_code),
            "name": check_zim_name(f"gutenberg_{lang_code}_all"),
            "periodicity": "quarterly",
            "tags": ["gutenberg"],
        }
        for lang_code in lang_codes
    ]
