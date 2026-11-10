import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup, Tag

from recipesauto.context import Context
from recipesauto.utils import check_zim_name, get_iso_639_3_code

context = Context.get()


def get_recipe_tag() -> str:
    return "gutenberg"


@dataclass
class Shelve:
    letter: str
    label: str


def get_en_shelves() -> list[Shelve]:
    resp = requests.get(
        "https://raw.githubusercontent.com/openzim/papers/refs/heads/main/locales/en.json",
        allow_redirects=True,
        timeout=context.http_timeout,
    )
    resp.raise_for_status()
    data = resp.json()
    ref_data = get_ref_data()
    return [
        Shelve(letter=letter, label=label)
        for letter, label in data["gutenberg"]["collections"].items()
        # the papers locale still lists "C", "D", "E" and "F" individually even
        # though papers2zim merges them into a single "CDEF" shelf ; skip those
        # individual ones since we only maintain a recipe for the merged shelf
        if f"en_lcc_{letter.lower()}" in ref_data
    ]


def get_all_lang_codes() -> list[str]:
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

    return [
        option["value"]
        for option in select_tag.find_all("option")
        if option.get("value")  # skips empty string or missing value
    ]


def shorthen_shelve_label(label: str, max_len: int = 58):
    if len(label) < max_len:
        return label
    short_label = label
    while len(short_label) > max_len - 1:
        last_cut = short_label.rfind(" ")
        if last_cut == -1:
            raise Exception(
                f"Impossible to make '{label}' fit inside {max_len} characters"
            )
        short_label = short_label[:last_cut]
    return f"{short_label}…"


SPECIAL_ZIM_LANGUAGES = {
    "fur": "fvr",
    "gla": "gla",
    "nap": "nap",
    "oji": "oji",
}


def get_ref_data() -> dict[str, Any]:
    return json.loads((Path(__file__).parent / "gutenberg.json").read_text())


def get_expected_recipes() -> list[dict[str, Any]]:
    lang_codes = get_all_lang_codes()
    en_shelves = get_en_shelves()
    ref_data = get_ref_data()

    return [
        {
            "category": "gutenberg",
            "config": {
                "offliner": {
                    "source": "gutenberg",
                    "lcc-shelves": "all",
                    "languages": lang_code,
                    "with-author-bio": True,
                    "with-author-portrait": True,
                    "publisher": "openZIM",
                    "offliner_id": "papers",
                    "stats-filename": "/output/task_progress.json",
                    "zim-languages": SPECIAL_ZIM_LANGUAGES.get(lang_code),
                    "optimization-cache": context.values["gutenberg_optim_url"],
                },
                "monitor": False,
                "platform": "gutenberg",
                "image": {"name": "ghcr.io/openzim/papers", "tag": "1.1.0"},
                "resources": {"cpu": 3, "disk": 322122547200, "memory": 16106127360},
                "warehouse_path": "/gutenberg",
            },
            # force nah despite lang code being unrecognized in pycountry
            # disable recipes with unknown language
            # disable yi (Yiddish) which contains only an audio book so far (not Zimmed)
            "enabled": lang_code in ["nah"]
            or (
                get_iso_639_3_code(lang_code) is not None
                and lang_code not in ["yi", "lt"]
            ),
            "language": get_iso_639_3_code(lang_code)
            or "mul",  # random lang, it is not enabled anyway
            "name": check_zim_name(f"gutenberg_{lang_code}_all"),
            "periodicity": "quarterly",
            "tags": ["gutenberg"],
            "archived": False,
            "context": "",
            "offliner": "papers",
            "version": "1.1.0",
        }
        for lang_code in lang_codes
    ] + [
        {
            "category": "gutenberg",
            "config": {
                "offliner": {
                    "source": "gutenberg",
                    "lcc-shelves": shelve.letter,
                    "zim-title": "Project Gutenberg Library",
                    "zim-desc": ref_data[f"en_lcc_{shelve.letter.lower()}"][
                        "description"
                    ],
                    "zim-long-desc": ref_data[f"en_lcc_{shelve.letter.lower()}"][
                        "long_description"
                    ],
                    "languages": "en",
                    "with-author-bio": True,
                    "with-author-portrait": True,
                    "publisher": "openZIM",
                    "offliner_id": "papers",
                    "stats-filename": "/output/task_progress.json",
                    "zim-name": check_zim_name(
                        f"gutenberg_en_lcc-{shelve.letter.lower()}"
                    ),
                    "optimization-cache": context.values["gutenberg_optim_url"],
                },
                "monitor": False,
                "platform": "gutenberg",
                "image": {"name": "ghcr.io/openzim/papers", "tag": "1.1.0"},
                "resources": {"cpu": 3, "disk": 322122547200, "memory": 16106127360},
                "warehouse_path": "/gutenberg",
            },
            "enabled": True,
            "language": "eng",
            "name": check_zim_name(f"gutenberg_en_lcc-{shelve.letter.lower()}"),
            "periodicity": "quarterly",
            "tags": ["gutenberg"],
            "archived": False,
            "context": "",
            "offliner": "papers",
            "version": "1.1.0",
        }
        for shelve in en_shelves
    ]
