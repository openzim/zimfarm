#!/usr/bin/env python3
# vim: ai ts=4 sts=4 et sw=4 nu

import logging

from zimfarm_backend.db import Session
from zimfarm_backend.utils.scheduling import request_tasks_using_schedule

logging.basicConfig(
    level=logging.DEBUG, format="[%(name)s - %(asctime)s: %(levelname)s] %(message)s"
)
logger = logging.getLogger("periodic-scheduler")


def main():
    logger.info("running periodic scheduler")

    with Session.begin() as session:
        request_tasks_using_schedule(session)


if __name__ == "__main__":
    main()
