#!/usr/bin/env python3

"""update scraper version for all recipes and unstarted tasks

./update_scraper_version.py mwoffliner 1.2.4"""

import sys

import sqlalchemy as sa
from sqlalchemy.orm import Session as OrmSession
from sqlalchemy.orm.attributes import flag_modified

from zimfarm_backend import logger
from zimfarm_backend.db import Session
from zimfarm_backend.db.models import RequestedTask, Schedule


def update_scraper_tag(session: OrmSession, scraper: str, tag: str):
    print(f"setting {scraper} {tag=}")  # noqa: T201

    nums: dict[str, int] = {}
    for model in (Schedule, RequestedTask):
        nums[model.__name__] = 0

        for entry in session.execute(
            sa.select(model).filter(
                model.config["offliner"]["offliner_id"].astext == scraper
            )
        ).scalars():
            # print(entry.config["task_name"], entry.config["image"])
            entry.config["image"]["tag"] = tag
            flag_modified(entry, "config")
            nums[model.__name__] += 1

    logger.info(
        "modified " + ", ".join({f"{num} {name}(s)" for name, num in nums.items()})
    )


if __name__ == "__main__":
    try:
        scraper, tag = sys.argv[1:]
    except (IndexError, ValueError):
        logger.error(f"Usage: {sys.argv[0]} SCRAPER_NAME VERSION_TAG")
        sys.exit(1)

    with Session.begin() as session:
        update_scraper_tag(session=session, scraper=scraper, tag=tag)
    logger.info("FINISH!")
