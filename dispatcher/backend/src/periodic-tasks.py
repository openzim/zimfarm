#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import logging

from common.mongo import Schedules

logger = logging.getLogger("periodic-tasks")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter("[%(name)s - %(asctime)s: %(levelname)s] %(message)s")
)
logger.addHandler(handler)


def main():
    logger.info("running periodic tasks")
    nb = Schedules().count_documents({})
    logger.debug(f"We have {nb} schedules…")


if __name__ == "__main__":
    main()
