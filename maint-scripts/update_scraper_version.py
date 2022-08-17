#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

""" update scrapver version for all recipes and unstarted tasks

    ./update_scraper_version.py mwoffliner 1.2.4
"""

import os
import sys

from pymongo import MongoClient


def update_scraper_tag(scraper: str, tag: str):
    print(f"setting {scraper} tag: {tag}")
    schedules = client["Zimfarm"]["schedules"]
    requested_tasks = client["Zimfarm"]["requested_tasks"]

    update = {"config.image.tag": tag}

    result = schedules.update_many({"config.task_name": scraper}, {"$set": update})
    print("schedules updated:", result.matched_count)
    result = requested_tasks.update_many(
        {"status": "requested", "config.task_name": scraper},
        {"$set": update},
    )
    print("requested_tasks updated:", result.matched_count)


if __name__ == "__main__":
    try:
        scraper = sys.argv[1]
        tag = sys.argv[2]
    except IndexError:
        print("You need to pass a scraper name and version tag")
        sys.exit(1)

    with MongoClient(os.getenv("ZF_MONGO_URI")) as client:
        update_scraper_tag(scraper=scraper, tag=tag)
    print("FINISH!")
