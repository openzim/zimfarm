import json
import re
from typing import Any
from urllib.parse import urljoin

import requests

from recipesauto.context import Context
from recipesauto.utils import check_zim_name

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
                    "logo-format": (_get_icon_url_for_slug(item["slug"])),
                    "output": "/output",
                    "slug": item["slug"],
                    "file-name-format": f'devdocs_en_{_get_cleaned(_get_slug_with_version(item["slug"]))}'
                    + "_{period}",
                    "name-format": check_zim_name(
                        f'devdocs_en_{_get_cleaned(_get_slug_with_version(item["slug"]))}'
                    ),
                    "description-format": f'{item["name"]} documentation, by DevDocs',
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
                "warehouse_path": "/devdocs",
            },
            "enabled": True,
            "language": {
                "code": "en",
                "name_en": "English",
                "name_native": "English",
            },
            "name": f'devdocs_en_{_get_cleaned(_get_slug_with_version(item["slug"]))}',
            "periodicity": "quarterly",
            "tags": [
                "devdocs",
            ],
        }
        for item in group_items_by_type(items)
    ]


def _get_icon_url_for_slug(slug: str) -> str:
    slug_no_version = _get_slug_with_version(slug)
    if slug_no_version == "moment_timezone":
        filename = "moment"
    elif slug_no_version == "vue_router":
        filename = "vue"
    elif slug_no_version == "tensorflow_cpp":
        filename = "tensorflow"
    elif slug_no_version in ["sanctuary_def", "sanctuary_type_classes"]:
        filename = "sanctuary"
    elif slug_no_version in [
        "minitest",
        "xslt_xpath",
        "nginx_lua_module",
        "liquid",
        "browser_support_tables",
        "web_extensions",
        "tcl_tk",
        "enzyme",
        "graphite",
        "mongoose",
    ]:
        filename = "_generic"
    else:
        filename = slug_no_version
    return f"https://drive.farm.openzim.org/devdocs/{filename}.png"


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


def _get_cleaned(value: str) -> str:
    return re.sub(r"[^.a-zA-Z0-9]", "-", value)


def _get_slug_with_version(slug: str) -> str:
    return slug.split("~", maxsplit=1)[0]
