import json
import unicodedata
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup, Tag

from recipesauto.constants import logger
from recipesauto.context import Context
from recipesauto.utils import check_zim_name, get_iso_639_3_code

context = Context.get()


def get_recipe_tag() -> str:
    return "onemorelibrary"


# languages supported by papers2zim's onemorelibrary source, as advertised on
# onemorelibrary.com/index.php/en/languages (see LANGUAGE_CODES in
# https://github.com/openzim/papers/blob/main/scraper/src/papers2zim/sources/onemorelibrary/languages.py)
LANGUAGES = ["en", "es", "fr", "de", "it", "ar", "ru", "fi", "sv", "la", "grc"]

# autonyms (site-displayed language labels) papers2zim's onemorelibrary source
# currently knows how to map to a language code ; mirrors the keys of
# LANGUAGE_CODES in the papers repo linked above
KNOWN_LANGUAGE_AUTONYMS = {
    "english",
    "español",
    "français",
    "deutsch",
    "italiano",
    "العربية",
    "русский",
    "suomi",
    "svenska",
    "lingua latīna",
    "latina",
    "latin",
    "αρχαία ελληνική γλώσσα",
    "ancient greek",
}

LANGUAGES_PAGE_URL = "https://onemorelibrary.com/index.php/en/languages"


def _normalize_autonym(name: str) -> str:
    return unicodedata.normalize("NFC", name).strip().casefold()


def warn_about_unknown_languages() -> None:
    """Warn if onemorelibrary.com advertises a language papers2zim's
    onemorelibrary source cannot map to a code yet (it only recognizes the
    site's language autonyms through a hardcoded mapping, unlike e.g.
    Gutenberg which accepts arbitrary ISO codes) ; the scraper's LANGUAGE_CODES
    then LANGUAGES/onemorelibrary.json here both need to be updated by hand.
    """
    try:
        resp = requests.get(
            LANGUAGES_PAGE_URL,
            allow_redirects=True,
            timeout=context.http_timeout,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        category_block = soup.find("div", class_="dj-category")
        if not isinstance(category_block, Tag):
            raise Exception("Bad HTML document")
        autonyms = {
            link.get_text(strip=True)
            for link in category_block.find_all("a", href=True)
            if "/languages/" in link["href"]
        }
    except Exception as exc:
        logger.warning(f"Could not check onemorelibrary.com for new languages: {exc}")
        return

    for autonym in autonyms:
        if _normalize_autonym(autonym) not in KNOWN_LANGUAGE_AUTONYMS:
            logger.warning(
                f"onemorelibrary.com now advertises language '{autonym}' which "
                "papers2zim's onemorelibrary source does not map to a language "
                "code yet ; update LANGUAGE_CODES in papers, then LANGUAGES "
                "(and onemorelibrary.json) here"
            )


def get_ref_data() -> dict[str, Any]:
    return json.loads((Path(__file__).parent / "onemorelibrary.json").read_text())


def get_expected_recipes() -> list[dict[str, Any]]:
    warn_about_unknown_languages()
    ref_data = get_ref_data()

    language_recipes = [
        {
            "category": "onemorelibrary",
            "config": {
                "offliner": {
                    "source": "onemorelibrary",
                    "languages": lang,
                    "zim-name": check_zim_name(f"onemorelibrary.com_{lang}_all"),
                    "zim-title": ref_data[lang]["title"],
                    "zim-desc": ref_data[lang]["description"],
                    "no-index": True,
                    "publisher": "openZIM",
                    "offliner_id": "papers",
                    "stats-filename": "/output/task_progress.json",
                    "optimization-cache": context.values["onemorelibrary_optim_url"],
                },
                "monitor": False,
                # no dedicated "onemorelibrary" platform exists (yet) to throttle
                # concurrency on, same as the existing mul_all recipe
                "platform": None,
                "image": {"name": "ghcr.io/openzim/papers", "tag": "1.2.0"},
                "resources": {"cpu": 3, "disk": 268435456000, "memory": 8589934592},
                "warehouse_path": "/gutenberg",
            },
            "enabled": True,
            "language": get_iso_639_3_code(lang) or "mul",
            "name": check_zim_name(f"onemorelibrary.com_{lang}_all"),
            "periodicity": "quarterly",
            "tags": ["onemorelibrary"],
            "archived": False,
            "context": "",
            "offliner": "papers",
            "version": "dev",
        }
        for lang in LANGUAGES
    ]

    mul_recipe = {
        "category": "onemorelibrary",
        "config": {
            "offliner": {
                "source": "onemorelibrary",
                "zim-name": check_zim_name("onemorelibrary.com_mul_all"),
                "zim-title": "One More Library",
                "zim-desc": (
                    "One of the largest and oldest online libraries of public "
                    "books in the world"
                ),
                "no-index": True,
                "publisher": "openZIM",
                "offliner_id": "papers",
                "stats-filename": "/output/task_progress.json",
                "optimization-cache": context.values["onemorelibrary_optim_url"],
            },
            "monitor": False,
            "platform": None,
            "image": {"name": "ghcr.io/openzim/papers", "tag": "1.2.0"},
            "resources": {"cpu": 3, "disk": 268435456000, "memory": 8589934592},
            "warehouse_path": "/gutenberg",
        },
        "enabled": True,
        "language": "mul",
        "name": check_zim_name("onemorelibrary.com_mul_all"),
        "periodicity": "quarterly",
        "tags": ["onemorelibrary", "multi"],
        "archived": False,
        "context": "",
        "offliner": "papers",
        "version": "dev",
    }

    return [*language_recipes, mul_recipe]
