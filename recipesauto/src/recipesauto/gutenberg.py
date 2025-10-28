from typing import Any

import requests
from bs4 import BeautifulSoup, Tag

from recipesauto.context import Context
from recipesauto.utils import check_zim_name, get_iso_639_3_code

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
                "offliner": {
                    "lcc-shelves": "all",
                    "languages": lang_code,
                    "publisher": "openZIM",
                    "offliner_id": "gutenberg",
                    "stats-filename": "/output/task_progress.json",
                },
                "monitor": False,
                "platform": "gutenberg",
                "image": {"name": "ghcr.io/openzim/gutenberg", "tag": "3.0.0"},
                "resources": {"cpu": 3, "disk": 322122547200, "memory": 16106127360},
                "warehouse_path": "/gutenberg",
            },
            # disable recipes with unknown language
            # disable yi (Yiddish) which contains only an audio book so far (not Zimmed)
            "enabled": get_iso_639_3_code(lang_code) is not None and lang_code != "yi",
            "language": get_iso_639_3_code(lang_code)
            or "qqq",  # random lang, it is not enabled anyway
            "name": check_zim_name(f"gutenberg_{lang_code}_all"),
            "periodicity": "quarterly",
            "tags": ["gutenberg"],
            "archived": False,
            "context": "",
            "offliner": "gutenberg",
            "version": "3.0.0",
        }
        for lang_code in lang_codes
    ]
