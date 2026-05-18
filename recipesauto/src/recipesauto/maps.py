import dataclasses
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag

from recipesauto.constants import logger
from recipesauto.context import Context

context = Context.get()


@dataclass(frozen=True, unsafe_hash=True)
class Area:
    name: str
    poly_url: str


def get_recipe_tag() -> str:
    return "openstreetmap"


def get_areas(page: str, level: int) -> list[Area]:
    areas: list[Area] = []
    resp = requests.get(
        page,
        allow_redirects=True,
        timeout=context.http_timeout,
    )
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "lxml")

    details_div = soup.find("div", id="details")
    if details_div:
        if not isinstance(details_div, Tag):
            raise Exception("Unexpected HTML document: details_div is not a tag")
        details_div.decompose()

    subregion_table = soup.find("table", id="subregions")

    if not isinstance(subregion_table, Tag):
        raise Exception("Unexpected HTML document: subregion_table is not a tag")

    subregions = subregion_table.find_all("td", class_="subregion")

    for subregion in subregions:
        link = subregion.find("a")
        if not isinstance(link, Tag):
            raise Exception("Unexpected HTML document: link is not a tag")

        name = link.string

        if not name:
            raise Exception("Unexpected HTML document: name is empty")

        html = urljoin(page, link["href"])  # pyright: ignore[reportArgumentType]
        poly = html.replace(".html", ".poly")

        areas.append(Area(name, poly_url=poly))

        if level > 0:  # only include continents + countries
            continue

        if name.lower() == "antarctica":  # antarctica has no subregion
            continue

        areas.extend(get_areas(page=html, level=level + 1))

    return areas


def get_expected_recipes() -> list[dict[str, Any]]:
    maps_area_file = Path(__file__).parent / "maps_areas.json"
    if maps_area_file.exists():
        areas = [Area(**data) for data in json.loads(maps_area_file.read_bytes())]
        logger.info(f"Reusing {len(areas)} areas from cache")
    else:
        page = "https://download.geofabrik.de/"
        areas = get_areas(page, 0)
        logger.info(f"{len(areas)} areas found online")
        maps_area_file.write_text(
            json.dumps([dataclasses.asdict(area) for area in areas])
        )

    areas.append(Area("all", ""))

    def get_name(value: str) -> str:
        return f"maps_en_{_get_cleaned(value)}"

    def get_scraper_version(name: str) -> str:
        return "dev" if name in ("maps_en_all", "maps_en_india") else "0.1.1"

    def _get_cleaned(value: str) -> str:
        return re.sub(r"[^.a-zA-Z0-9]+", "-", value).strip("-").lower()

    config_data = json.loads((Path(__file__).parent / "maps.json").read_text())

    return [
        {
            "category": "maps",
            "config": {
                "offliner": {
                    flag: value
                    for flag, value in {
                        "publisher": "openZIM",
                        "stats-filename": "/output/task_progress.json",
                        "output": "/output",
                        "title": config_data[get_name(area.name)]["title"],
                        "description": config_data[get_name(area.name)]["description"],
                        "default-view": config_data[get_name(area.name)].get(
                            "default_view"
                        ),
                        "name": config_data[get_name(area.name)].get("name")
                        or get_name(area.name),
                        "include-poly": area.poly_url,
                        "offliner_id": "maps",
                    }.items()
                    if value
                },
                "monitor": False,
                "platform": None,
                "image": {
                    "name": "ghcr.io/openzim/maps",
                    "tag": get_scraper_version(get_name(area.name)),
                },
                "resources": config_data[get_name(area.name)]["resources"],
                "warehouse_path": "",
            },
            "enabled": True,
            "language": "eng",
            "name": config_data[get_name(area.name)].get("name") or get_name(area.name),
            "periodicity": "manually",
            "tags": ["openstreetmap"],
            "archived": False,
            "context": "",
            "offliner": "maps",
            "version": get_scraper_version(get_name(area.name)),
        }
        for area in areas
        if get_name(area.name) in config_data
    ]
