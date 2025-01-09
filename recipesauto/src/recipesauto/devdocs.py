import json
import re
from typing import Any
from urllib.parse import urljoin

import requests

from recipesauto.context import Context

context = Context.get()

DEVDOCS_DOCS = "https://devdocs.io/docs.json"


def get_recipe_tag() -> str:
    return "devdocs"


def get_expected_recipes() -> list[dict[str, Any]]:
    resp = requests.get(
        DEVDOCS_DOCS,
        timeout=context.http_timeout,
    )
    resp.raise_for_status()

    items = resp.json()

    return [
        {
            "category": "devdocs",
            "config": {
                "flags": {
                    "logo-format": f'https://drive.farm.openzim.org/devdocs/{_get_slug_with_version(item["slug"])}.png',
                    "output": "/output",
                    "slug": item["slug"],
                    "file-name-format": f'devdocs_en_{_get_slug_with_version(item["slug"])}'
                    + "_{period}",
                    "name-format": f'devdocs_en_{_get_slug_with_version(item["slug"])}',
                    "description-format": f'{item["name"]} docs by DevDocs',
                    "title-format": f'{item["name"]} Docs',
                    "publisher": "openZIM",
                },
                "image": {
                    "name": "ghcr.io/openzim/devdocs",
                    "tag": "0.2.0",
                },
                "monitor": False,
                "platform": "devdocs",
                "resources": {
                    "cpu": 1,
                    "disk": 536870912,
                    "memory": 2147483648,
                },
                "task_name": "devdocs",
                # force creation in dev, we are not yet in prod
                # "warehouse_path": "/devdocs",
                "warehouse_path": "/.hidden/dev",
            },
            "enabled": True,
            "language": {
                "code": "en",
                "name_en": "English",
                "name_native": "English",
            },
            "name": f'devdocs_en_{_get_slug_with_version(item["slug"])}',
            # force manually periodicity, we are not yet in prod
            # "periodicity": "quarterly",
            "periodicity": "manually",
            "tags": [
                "devdocs",
            ],
        }
        for item in group_items_by_type(items)
    ]


def group_items_by_type(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    names = set([item["name"] for item in items])
    return [definition_for_name(items=items, name=name) for name in names]


def definition_for_name(items: list[dict[str, Any]], name: str) -> dict[str, Any]:
    if name == "GCC":
        # Do not publish GCC CPP for now
        variants = filter(
            lambda item: item["name"] == name and "CPP" not in item["version"], items
        )
    elif name in ("Haxe", "Ansible"):
        # Choose "generic" version of the doc
        variants = filter(
            lambda item: item["name"] == name and not item["version"], items
        )
    elif name == "RethinkDB":
        # arbitrarily choose javascript version of the doc
        variants = filter(
            lambda item: item["name"] == name and "javascript" in item["version"], items
        )
    else:
        variants = filter(lambda item: item["name"] == name, items)
    variant = list(
        sorted(
            variants, key=lambda variant: variant.get("release", "aaa"), reverse=True
        )
    )[0]
    print(f'{name}: {variant["slug"]}')
    return {"name": name, "slug": variant["slug"]}


def _get_slug_with_version(slug: str) -> str:
    return slug.split("~", maxsplit=1)[0]
