#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import logging

from utils.scheduling import request_tasks_using_schedule

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("periodic-scheduler")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter("[%(name)s - %(asctime)s: %(levelname)s] %(message)s")
)
logger.addHandler(handler)


def main():
    logger.info("running periodic scheduler")

    request_tasks_using_schedule()


if __name__ == "__main__":
    main()
