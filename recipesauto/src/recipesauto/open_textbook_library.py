import json
from pathlib import Path
from typing import Any

from recipesauto.context import Context
from recipesauto.utils import check_zim_name, get_iso_639_3_code

context = Context.get()


def get_recipe_tag() -> str:
    return "open-textbook-library"


# Languages with actual valid, ZIM-able books in Open Textbook Library.
#
# This is narrower than simply tallying the "language" field across every
# catalog entry (see https://open.umn.edu/opentextbooks/textbooks.json):
# some languages only show up on books that end up with no valid content to
# include once papers2zim actually resolves them (e.g. no downloadable
# format, license issue, ...). The authoritative source is papers2zim's own
# generated "bookLanguages" metadata from a real scrape of the full (mul)
# catalog ; see https://github.com/openzim/zimfarm/issues/2111.
LANGUAGES = [
    "az",
    "bg",
    "de",
    "el",
    "en",
    "es",
    "fr",
    "ja",
    "ko",
    "nl",
    "ru",
    "sl",
    "uk",
    "zh",
]


def get_ref_data() -> dict[str, Any]:
    return json.loads(
        (Path(__file__).parent / "open_textbook_library.json").read_text()
    )


def get_expected_recipes() -> list[dict[str, Any]]:
    ref_data = get_ref_data()

    language_recipes = [
        {
            "category": "open-textbook-library",
            "config": {
                "offliner": {
                    "source": "opentextbooks",
                    "languages": lang,
                    "zim-name": check_zim_name(f"open-textbook-library_{lang}_all"),
                    "zim-title": ref_data[lang]["title"],
                    "zim-desc": ref_data[lang]["description"],
                    "publisher": "openZIM",
                    "offliner_id": "papers",
                    "stats-filename": "/output/task_progress.json",
                    "optimization-cache": context.values[
                        "open_textbook_library_optim_url"
                    ],
                },
                "monitor": False,
                # no dedicated "open-textbook-library" platform exists (yet)
                "platform": None,
                "image": {"name": "ghcr.io/openzim/papers", "tag": "1.2.0"},
                "resources": {
                    "cpu": 3,
                    "disk": 2147483648,
                    "memory": 4294967296,
                    "shm": 4294967296,
                },
                "warehouse_path": "/gutenberg",
            },
            "enabled": True,
            "language": get_iso_639_3_code(lang) or "mul",
            "name": check_zim_name(f"open-textbook-library_{lang}_all"),
            "periodicity": "manually",
            "tags": ["open-textbook-library"],
            "archived": False,
            "context": "",
            "offliner": "papers",
            "version": "dev",
        }
        for lang in LANGUAGES
    ]

    mul_recipe = {
        "category": "open-textbook-library",
        "config": {
            "offliner": {
                "source": "opentextbooks",
                "zim-name": check_zim_name("open-textbook-library_mul_all"),
                "zim-title": "Open Textbook Library",
                "zim-desc": (
                    "The whole collection of open textbooks by Open Education Network"
                ),
                "publisher": "openZIM",
                "offliner_id": "papers",
                "stats-filename": "/output/task_progress.json",
                "optimization-cache": context.values["open_textbook_library_optim_url"],
            },
            "monitor": False,
            "platform": None,
            "image": {"name": "ghcr.io/openzim/papers", "tag": "1.2.0"},
            "resources": {
                "cpu": 3,
                "disk": 2147483648,
                "memory": 4294967296,
                "shm": 4294967296,
            },
            "warehouse_path": "/gutenberg",
        },
        "enabled": True,
        "language": "mul",
        "name": check_zim_name("open-textbook-library_mul_all"),
        "periodicity": "manually",
        "tags": ["open-textbook-library"],
        "archived": False,
        "context": "",
        "offliner": "papers",
        "version": "dev",
    }

    return [*language_recipes, mul_recipe]
