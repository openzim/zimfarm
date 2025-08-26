import json
import os
import sys
from http import HTTPStatus

import requests
from get_token import get_token, get_token_headers, get_url

from zimfarm_backend import logger
from zimfarm_backend.common.constants import REQUESTS_TIMEOUT

SEARCH_URL = "https://zenith-prod-alt.ted.com/api/search"
TED_INDEX_NAME = "coyote_models_acme_videos_alias_38ce41d1f97ca56a38068f613af166da"


def get_ted_topics() -> set[str]:
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
        timeout=REQUESTS_TIMEOUT,
    )
    req.raise_for_status()
    topics = json.loads(req.content)["results"][0]["facets"]["tags"].keys()
    logger.info(f"{len(topics)} topics found")
    return set(topics)


def get_clean_ted_topic_name(ted_topic_name: str) -> str:
    return ted_topic_name.replace(" ", "-").replace("'", "")


def create_recipe(ted_topic_name: str, access_token: str):
    clean_ted_topic_name = get_clean_ted_topic_name(ted_topic_name)
    schedule_name = f"ted_topic_{clean_ted_topic_name}"
    response = requests.get(
        get_url(f"/schedules/{schedule_name}"),
        headers=get_token_headers(access_token),
        timeout=REQUESTS_TIMEOUT,
    )
    if response.status_code == HTTPStatus.OK:
        logger.warning(f"Recipe {schedule_name} already exists, ignoring.")
        return

    if response.status_code != HTTPStatus.NOT_FOUND:
        response.raise_for_status()

    logger.info(f"Creating recipe for {ted_topic_name}")

    data = {
        "category": "ted",
        "config": {
            "offliner": {
                "offliner_id": "ted",
                "description": f"A collection of TED videos about {ted_topic_name}",
                "title": f"TED {ted_topic_name}",
                "topics": ted_topic_name,
                "name": f"ted_mul_{clean_ted_topic_name}",
                "languages": "eng,fra,esp,deu,chi",
                "format": "webm",
                "low-quality": True,
                "optimization-cache": os.environ["TED_OPTIM_CACHE_URL"],
                "output": "/output",
                "tmp-dir": "/output",
                "subtitles": "all",
                "subtitles-enough": True,
                "debug": True,
                "tags": "ted",
            },
            "image": {
                "name": "ghcr.io/openzim/ted",
                "tag": "3.0.2",
            },
            "monitor": False,
            "platform": "ted",
            "resources": {
                "cpu": 3,
                "disk": 32212254720,
                "memory": 2147483648,
            },
            "warehouse_path": "/.hidden/dev",
        },
        "enabled": True,
        "language": "mul",
        "name": schedule_name,
        "periodicity": "quarterly",
        "tags": [
            "ted-by-topic",
        ],
    }
    response = requests.post(
        get_url("/schedules/"),
        headers=get_token_headers(access_token),
        json=data,
        timeout=REQUESTS_TIMEOUT,
    )
    if response.status_code != HTTPStatus.CREATED:
        logger.error(json.loads(response.content))
        response.raise_for_status()


def get_existing_recipes_topics(access_token: str) -> set[str]:
    skip = 0
    per_page = 200

    topics: set[str] = set()
    while True:
        response = requests.get(
            get_url(f"/schedules/?limit={per_page}&skip={skip}&tag=ted-by-topic"),
            headers=get_token_headers(access_token),
            timeout=REQUESTS_TIMEOUT,
        )
        response.raise_for_status()

        schedules = response.json()
        topics.update({schedule["name"][10:] for schedule in schedules["items"]})

        if (
            schedules["meta"]["limit"] + schedules["meta"]["skip"]
            < schedules["meta"]["count"]
        ):
            skip += per_page
        else:
            break

    return topics


def main(zf_username: str, zf_password: str):
    """Creates recipes for TED by topics"""

    access_token, _ = get_token(zf_username, zf_password)

    existing_recipes_topics = get_existing_recipes_topics(access_token=access_token)
    logger.debug(",".join(sorted(existing_recipes_topics)))
    exisiting_online_topics = get_ted_topics()
    logger.debug(",".join(sorted(exisiting_online_topics)))

    recipes_to_create = [
        topic
        for topic in exisiting_online_topics
        if get_clean_ted_topic_name(topic) not in existing_recipes_topics
    ]
    logger.info(f"*** Recipes to create: {','.join(sorted(recipes_to_create))}")
    recipes_to_delete = [
        topic
        for topic in existing_recipes_topics
        if not any(
            get_clean_ted_topic_name(topic2) == topic
            for topic2 in exisiting_online_topics
        )
        and topic != "all"
    ]

    for topic in recipes_to_create:
        create_recipe(ted_topic_name=topic, access_token=access_token)

    logger.info(
        f"*** Recipes to delete manually: {','.join(sorted(recipes_to_delete))}"
    )


if __name__ == "__main__":
    if len(sys.argv) != 3:  # noqa: PLR2004
        logger.error(
            "Incorrect number of arguments\n"
            f"Usage: {sys.argv[0]} <zf_username> <zf_password>\n"
            "TED_OPTIM_CACHE_URL environment variable must be set to the optimization"
            " cache URL to use"
        )
        sys.exit(1)

    if "TED_OPTIM_CACHE_URL" not in os.environ:
        logger.error(
            "TED_OPTIM_CACHE_URL environment variable must be set to the optimization"
            " cache URL to use in recipes"
        )
        sys.exit(2)
    args = sys.argv[1:]
    main(*args)
