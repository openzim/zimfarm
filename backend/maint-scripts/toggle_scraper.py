#!/usr/bin/env python3
# vim: ai ts=4 sts=4 et sw=4 nu

"""enable of disable schedules for a specific scraper. Also removes requested tasks

./toggle_scraper.py enable
./toggle_scraper.py disable
"""

import os
import sys

from pymongo import MongoClient

from zimfarm_backend import logger


def toggle_scraper(scraper: str, *, enable: bool):
    logger.info(f"setting {scraper} {enable=}")
    schedules = client["Zimfarm"][  # pyright: ignore[reportUnknownVariableType]
        "schedules"
    ]
    requested_tasks = client["Zimfarm"][  # pyright: ignore[reportUnknownVariableType]
        "requested_tasks"
    ]
    result = schedules.update_many(
        {"config.task_name": scraper}, {"$set": {"enabled": enable}}
    )
    logger.info("schedules updated:", result.matched_count)
    if not enable:
        result = requested_tasks.delete_many(
            {"status": "requested", "config.task_name": scraper}
        )
        logger.info("requested_tasks removed:", result.deleted_count)


if __name__ == "__main__":
    try:
        scraper = sys.argv[1]
        enable = sys.argv[2] == "enable"
    except IndexError:
        logger.error("You need to pass a scraper name and 'enable' or 'disable'")
        sys.exit(1)

    with MongoClient(
        os.getenv("ZF_MONGO_URI"),
    ) as client:  # pyright: ignore[reportUnknownVariableType]
        toggle_scraper(scraper=scraper, enable=enable)
    logger.info("FINISH!")
