from typing import Any

import requests

from recipesauto.context import Context
from recipesauto.utils import check_zim_name, get_language_data

context = Context.get()


def get_recipe_tag() -> str:
    return "phet"


def _ignore_locale(locale: str) -> bool:
    return locale in [
        "ba",
        "fu",
    ]  # both do not contain any translated simulation for now


def get_expected_recipes() -> list[dict[str, Any]]:

    resp = requests.get(
        "https://phet.colorado.edu/services/metadata/1.3/simulations?format=json&summary",
        headers={
            "Cookie": "phet-common-info=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
            "eyJsb2dnZWRJbiI6ZmFsc2UsImlhdCI6MTc0OTE5NDk2NiwiZXhwIjoxNzUxODMwMTY2fQ."
            "FhVrkk4qJsdRmYayQWUoiYEMQZa7qUNAWkA5Nm03iYo"
        },
        allow_redirects=True,
        timeout=context.http_timeout,
    )
    resp.raise_for_status()
    data = resp.json()
    locales = sorted(
        set(
            filter(
                lambda locale: locale == "zh_CN" or "_" not in locale,
                [
                    locale
                    for project in data["projects"]
                    for sim in project["simulations"]
                    for locale in sim["localizedSimulations"].keys()
                ],
            )
        )
    )
    del resp
    del data

    return [
        {
            "category": "phet",
            "config": {
                "flags": {
                    "includeLanguages": locale,
                    "withoutLanguageVariants": True,
                },
                "image": {
                    "name": "ghcr.io/openzim/phet",
                    "tag": "3.1.0",
                },
                "monitor": False,
                "resources": {
                    "cpu": 3,
                    "disk": 10737418240,
                    "memory": 7516192768,
                },
                "task_name": "phet",
                "platform": "phet",
                "warehouse_path": "/phet",
            },
            "enabled": True,
            "language": get_language_data(locale if locale != "zh_CN" else "zh"),
            "name": check_zim_name(_get_name(locale)),
            "periodicity": "quarterly",
            "tags": [
                "phet",
            ],
        }
        for locale in locales
        if not _ignore_locale(locale)
    ] + [
        {
            "category": "phet",
            "config": {
                "flags": {
                    "mulOnly": True,
                    "withoutLanguageVariants": True,
                },
                "image": {
                    "name": "ghcr.io/openzim/phet",
                    "tag": "3.1.0",
                },
                "monitor": False,
                "resources": {
                    "cpu": 3,
                    "disk": 10737418240,
                    "memory": 7516192768,
                },
                "task_name": "phet",
                "platform": "phet",
                "warehouse_path": "/phet",
            },
            "enabled": True,
            "language": {
                "code": "mul",
                "name_en": "Multiple Languages",
                "name_native": "Multiple Languages",
            },
            "name": check_zim_name(_get_name("mul")),
            "periodicity": "quarterly",
            "tags": [
                "multi",
                "customapp",
                "phet",
            ],
        }
    ]


def _get_name(locale: str) -> str:
    if locale == "zh_CN":
        return "phet_zh_all"
    else:
        return f"phet_{locale}_all"
