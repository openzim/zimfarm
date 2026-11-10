import json
from pathlib import Path
from typing import Any

from recipesauto.context import Context
from recipesauto.utils import check_zim_name, get_iso_639_3_code

context = Context.get()


def get_recipe_tag() -> str:
    return "open-textbook-library"


# languages observed in Open Textbook Library's own catalog (polled live via
# https://open.umn.edu/opentextbooks/textbooks.json, 2040 books as of writing),
# mapped to their standard ISO 639-1 code regardless of how few books exist in
# that language (per explicit choice: one recipe per language found, not just
# the most popular ones)
#
# IMPORTANT: as of writing, papers2zim's opentextbooks source does not
# actually filter by language yet (see https://github.com/openzim/papers/issues/180)
# so all these per-language recipes are kept disabled until that lands, to
# avoid running N recipes that would all produce the exact same full-catalog
# ZIM. Re-enable once the issue above is fixed and released.
LANGUAGES = [
    "en",
    "es",
    "fr",
    "nl",
    "de",
    "zh",
    "pl",
    "ko",
    "ja",
    "el",
    "pt",
    "bg",
    "ru",
    "az",
    "sl",
    "uk",
    "sw",
    "it",
    "ar",
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
