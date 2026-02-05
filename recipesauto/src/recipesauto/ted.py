import json
from typing import Any

import requests

from recipesauto.context import Context
from recipesauto.utils import check_zim_name

context = Context.get()

SEARCH_URL = "https://zenith-prod-alt.ted.com/api/search"
TED_INDEX_NAME = "coyote_models_acme_videos_alias_38ce41d1f97ca56a38068f613af166da"
MINIMUM_VIDEOS_NUMBER = 5


def get_recipe_tag() -> str:
    return "ted-by-topic"


TED_TAGS = {"gaming": "gaming", "conducting": "Music"}


def get_expected_recipes() -> list[dict[str, Any]]:
    data = [
        {
            "indexName": TED_INDEX_NAME,
            "params": {
                "attributeForDistinct": "objectID",
                "distinct": 1,
                "facets": ["subtitle_languages", "tags"],
                "highlightPostTag": "__/ais-highlight__",
                "highlightPreTag": "__ais-highlight__",
                "hitsPerPage": 1,
                "maxValuesPerFacet": 500,
                "page": 0,
                "query": "",
                "tagFilters": "",
            },
        }
    ]
    req = requests.post(
        SEARCH_URL,
        headers={"User-Agent": "Mozilla/5.0"},
        json=data,
        timeout=context.http_timeout,
    )
    req.raise_for_status()
    topics = [
        topic
        for topic, count in json.loads(req.content)["results"][0]["facets"][
            "tags"
        ].items()
        if count >= MINIMUM_VIDEOS_NUMBER  # do not consider too small topics
    ]
    return [
        {
            "category": "ted",
            "config": {
                "offliner": {
                    "description": f"A collection of TED videos about {topic}",
                    "title": f"TED {topic}",
                    "topics": topic,
                    "name": check_zim_name(f"ted_mul_{_get_clean_topic_name(topic)}"),
                    "format": "webm",
                    "low-quality": True,
                    "optimization-cache": context.values["ted_optim_url"],
                    "output": "/output",
                    "tmp-dir": "/output",
                    "subtitles": "all",
                    "publisher": "openZIM",
                    "offliner_id": "ted",
                    "tags": TED_TAGS.get(topic),
                },
                "image": {
                    "name": "ghcr.io/openzim/ted",
                    "tag": "3.1.0",
                },
                "monitor": False,
                "platform": "ted",
                "resources": {
                    "cpu": 3,
                    "disk": 32212254720,
                    "memory": 2147483648,
                },
                "warehouse_path": "/ted",
            },
            "enabled": True,
            "language": "mul",
            "name": f"ted_topic_{_get_clean_topic_name(topic)}",
            "periodicity": "quarterly",
            "tags": [
                "ted-by-topic",
            ],
            "version": "initial",
            "archived": False,
            "context": "",
            "offliner": "ted",
        }
        for topic in topics
    ]


def _get_clean_topic_name(ted_topic_name: str) -> str:
    clean_topic = ted_topic_name.replace(" ", "-").replace("'", "")
    if "lgbtqia+" in clean_topic:
        clean_topic = clean_topic.replace("lgbtqia+", "lgbtqia")
    if "español" in clean_topic:
        clean_topic = clean_topic.replace("español", "espanol")
    if "audacious-project" in clean_topic:
        clean_topic = "audacious-project"
    return clean_topic
