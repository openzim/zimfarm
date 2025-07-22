#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import argparse
import os
import sys

from common import logger
from common.constants import DEFAULT_WEB_API_URLS, DEFAULT_WORKDIR, WORKER_MANAGER
from manager.worker import WorkerManager


def main():
    parser = argparse.ArgumentParser(prog=WORKER_MANAGER)

    parser.add_argument(
        "--webapi-uri",
        help="zimfarm API URI",
        required=not bool(DEFAULT_WEB_API_URLS),
        default=[],
        dest="webapi_uris",
        action="append",
    )

    parser.add_argument(
        "--socket-uri",
        help="[obsolete] zimfarm websocket URI",
        required=False,
        dest="socket_uri",
    )

    parser.add_argument(
        "--username",
        help="username to authenticate to zimfarm",
        required=not bool(os.getenv("USERNAME")),
        default=os.getenv("USERNAME"),
    )

    parser.add_argument(
        "--workdir",
        help="directory in which workers create task-related files",
        required=not bool(DEFAULT_WORKDIR),
        default=DEFAULT_WORKDIR,
        dest="workdir",
    )

    parser.add_argument(
        "--name",
        help="name of this worker",
        dest="worker_name",
        required=not bool(os.getenv("WORKER_NAME")),
        default=os.getenv("WORKER_NAME"),
    )

    args = parser.parse_args()

    if not args.webapi_uris and DEFAULT_WEB_API_URLS:
        args.webapi_uris += DEFAULT_WEB_API_URLS

    logger.info(f"starting zimfarm {WORKER_MANAGER}.")
    try:
        manager = WorkerManager(
            username=args.username,
            webapi_uris=args.webapi_uris,
            workdir=args.workdir,
            worker_name=args.worker_name,
        )
        sys.exit(manager.run())
    except Exception as exc:
        logger.error(f"Unhandled exception: {exc}")
        logger.exception(exc)
        logger.error("exiting.")
        sys.exit(1)


if __name__ == "__main__":
    main()
