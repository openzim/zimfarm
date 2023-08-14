#!/usr/bin/env python3

""" update scraper version for all recipes and unstarted tasks

    ./update_scraper_version.py mwoffliner 1.2.4"""

import sys

import sqlalchemy as sa
import sqlalchemy.orm as so
from sqlalchemy.orm.attributes import flag_modified

import db.models as dbm
from db import dbsession


@dbsession
def update_scraper_tag(session: so.Session, scraper: str, tag: str):
    print(f"setting {scraper} {tag=}")

    nums = {}
    for model in (dbm.Schedule, dbm.RequestedTask):
        nums[model.__name__] = 0

        for entry in session.execute(
            sa.select(model).filter(model.config["task_name"].astext == scraper)
        ).scalars():
            # print(entry.config["task_name"], entry.config["image"])
            entry.config["image"]["tag"] = tag
            flag_modified(entry, "config")
            nums[model.__name__] += 1

    print("modified " + ", ".join({f"{num} {name}(s)" for name, num in nums.items()}))

    return


if __name__ == "__main__":
    try:
        scraper, tag = sys.argv[1:]
    except (IndexError, ValueError):
        print(f"Usage: {sys.argv[0]} SCRAPER_NAME VERSION_TAG")
        sys.exit(1)

    update_scraper_tag(scraper=scraper, tag=tag)
    print("FINISH!")
