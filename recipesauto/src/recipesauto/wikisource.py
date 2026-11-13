import json
from pathlib import Path
from typing import Any

from recipesauto.context import Context
from recipesauto.utils import get_iso_639_3_code

context = Context.get()


def get_recipe_tag() -> str:
    return "wikisource"


def get_ref_data() -> dict[str, Any]:
    return json.loads((Path(__file__).parent / "wikisource.json").read_text())


# Wikisource languages for which papers2zim's wikisource source (backed by
# ws-export.wmcloud.org's per-language OPDS feeds) actually has exported
# EPUBs today. Unlike Gutenberg/One More Library, ws-export has no
# enumerable/scriptable list of supported languages we could check (its
# OPDS index pages are behind Anubis bot-protection, and the underlying
# "Validated texts" category size is a poor proxy: e.g. "pl" has hundreds of
# thousands of validated pages but zero exported epubs).
#
# IMPORTANT: this list was established by manually checking
# https://ws-export.wmcloud.org/opds/ in a browser on 2026-11-12. It WILL go
# stale as more languages get export-ready texts ; re-check that page by
# hand and update this list accordingly, there is no way to automate it
# given the current state of ws-export (see comment above).
#
# All other wikisource_* recipes (still on mwoffliner) are intentionally
# left out of get_expected_recipes() below: they stay tagged "wikisource"
# but are not expected here, so processor.py's obsolete-recipe phase will
# archive them on the next --push run. That is the intended outcome: these
# languages have no export-ready content on ws-export.wmcloud.org, so their
# recipes should be paused (archived, not deleted) until that changes.
LANGUAGES = ["bn", "en", "fr", "pa", "te"]


def get_expected_recipes() -> list[dict[str, Any]]:
    ref_data = get_ref_data()

    return [
        {
            "category": "wikisource",
            "config": {
                "offliner": {
                    "source": "wikisource",
                    "languages": lang,
                    "zim-title": ref_data[lang]["title"],
                    "zim-desc": ref_data[lang]["description"],
                    "publisher": "openZIM",
                    "offliner_id": "papers",
                    "stats-filename": "/output/task_progress.json",
                    "optimization-cache": context.values["wikisource_optim_url"],
                },
                "monitor": False,
                "platform": "wikimedia",
                "image": {"name": "ghcr.io/openzim/papers", "tag": "1.2.0"},
                "resources": {"cpu": 3, "disk": 2147483648, "memory": 2147483648},
                "warehouse_path": "/wikisource",
            },
            "enabled": True,
            "language": get_iso_639_3_code(lang) or "mul",
            # note: does not match check_zim_name's pattern (it expects at
            # least 3 underscore-separated segments), but this is the
            # existing, live naming convention for all wikisource_* recipes
            "name": f"wikisource_{lang}",
            "periodicity": "quarterly",
            "tags": ["wikisource"],
            "archived": False,
            "context": "",
            "offliner": "papers",
            "version": "dev",
        }
        for lang in LANGUAGES
    ]
