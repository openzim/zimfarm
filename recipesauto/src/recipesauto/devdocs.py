import json
import re
from typing import Any
from urllib.parse import urljoin

import requests

from recipesauto.context import Context

context = Context.get()

DEVDOCS_HOMEPAGE = "https://devdocs.io"


def get_recipe_tag() -> str:
    return "devdocs"


def get_expected_recipes() -> list[dict[str, Any]]:
    resp = requests.get(
        DEVDOCS_HOMEPAGE,
        timeout=context.http_timeout,
    )
    resp.raise_for_status()

    # search for docs JS url
    match = re.findall(r'<script src="(\/assets\/docs-.*?\.js)"', resp.text)
    if not match:
        raise Exception("URL of JS docs not found")

    # get docs JS content
    resp = requests.get(
        urljoin(DEVDOCS_HOMEPAGE, match[0]),
        timeout=context.http_timeout,
    )
    resp.raise_for_status()

    # Extract the variable value using regex
    match = re.search(r"app\.DOCS\s*=\s*(\[.*\]);", resp.text, re.DOTALL)
    if not match:
        raise ValueError("Could not find the 'app.DOCS' variable in the file")

    # Extracted value as a string
    docs_string = match.group(1)

    # Convert the JavaScript-like object into valid JSON
    # Replace unquoted property names with quoted ones
    def make_valid_json(js_obj_str):

        # Replace unquoted keys with quoted keys
        js_obj_str = re.sub(
            r'(?<!["\'])\b([a-zA-Z_]\w*)\b(?=\s*:\s*(?:["\'{\d]|null))',
            r'"\1"',
            js_obj_str,
        )

        # Replace single-quoted and improperly escaped double-quoted values
        # Match values after a colon that are single or double-quoted
        js_obj_str = re.sub(
            r":(\'[^\']*?\')",  # Capture `:` and the quoted string
            lambda m: ':"' + m.group(1)[1:-1].replace('"', r"\"") + '"',  # Reformat
            js_obj_str,
        )

        # Replace \x with \\x
        js_obj_str = re.sub(r"\\x", r"\\\\x", js_obj_str)

        return js_obj_str

    docs_string = make_valid_json(docs_string)

    # Parse the string into a Python object
    docs_list = json.loads(docs_string)

    # `docs_list` is now a Python list of dictionaries

    return [
        {
            "category": "devdocs",
            "config": {
                "flags": {
                    "logo-format": f'https://drive.farm.openzim.org/devdocs/{_get_icon_name(item["slug"])}.png',
                    "output": "/output",
                    "slug": item["slug"],
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
            "name": f'devdocs_en_{_get_clean_slug(item["slug"])}',
            # force manually periodicity, we are not yet in prod
            # "periodicity": "quarterly",
            "periodicity": "manually",
            "tags": [
                "devdocs",
            ],
        }
        for item in docs_list
    ]


def _get_clean_slug(slug: str) -> str:
    return re.sub(r"[^.a-zA-Z0-9]", "-", slug)


def _get_icon_name(slug: str) -> str:
    return slug.split("~", maxsplit=1)[0]
