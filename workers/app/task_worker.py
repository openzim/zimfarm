#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import os
import sys
import argparse
import traceback

from common import logger
from task.worker import TaskWorker
from common.constants import DEFAULT_WEB_API_URL, TASK_WORKER


def main():
    parser = argparse.ArgumentParser(prog=TASK_WORKER)

    parser.add_argument(
        "--task-id", help="task-id to attempt to process", required=True, dest="task_id"
    )

    parser.add_argument(
        "--webapi-uri",
        help="zimfarm API URI",
        required=not bool(DEFAULT_WEB_API_URL),
        default=DEFAULT_WEB_API_URL,
        dest="webapi_uri",
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
        required=not bool(os.getenv("WORKDIR")),
        default=os.getenv("WORKDIR"),
        dest="workdir",
    )

    args = parser.parse_args()

    logger.info(f"starting zimfarm {TASK_WORKER} for {args.task_id}.")
    try:
        worker = TaskWorker(
            username=args.username,
            webapi_uri=args.webapi_uri,
            workdir=args.workdir,
            task_id=args.task_id,
        )
    except Exception as exc:
        logger.critical(f"Unhandled exception during init: {exc}")
        sys.exit(1)

    try:
        sys.exit(worker.run())
    except Exception as exc:
        logger.error(f"Unhandled exception: {exc}")
        logger.exception(exc)
        logger.error("exiting.")
        try:
            logger.info("Trying to upload exception details")
            tbe = traceback.TracebackException.from_exception(exc)
            worker.shutdown(
                "failed",
                exception="".join(tbe.format_exception_only()),
                traceback="".join(tbe.format()),
            )
        except Exception:
            logger.error("Could not submit failure details")
        sys.exit(1)


if __name__ == "__main__":
    main()
