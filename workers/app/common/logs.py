#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import re
import urllib
import logging
import datetime

from kiwixstorage import KiwixStorage

from common.docker import (
    ContainerLogsAsFile,
    start_uploader,
    wait_container,
    stop_container,
    remove_container,
    get_container_logs,
)

logger = logging.getLogger(__name__)


def upload_scraper_log(
    docker_client, task, username, scraper, task_workdir, host_task_workdir
):
    try:
        upload_uri = urllib.parse.urlparse(task["upload"]["logs"]["upload_uri"])
    except Exception as exc:
        logger.error(f"Failed to parse logs upload_uri. Can't upload logs. {exc}")
        return False, None

    filename = f"{task['_id']}.log"
    if upload_uri.scheme == "s3":
        uploaded = upload_log_to_s3(
            docker_client,
            scraper.name,
            upload_uri=re.sub(r"^s3:", "https:", upload_uri.geturl(), 1),
            key=filename,
            delete_after=task["upload"]["logs"]["expiration"],
        )
    else:
        uploaded = upload_log_to_server(
            docker_client,
            scraper.name,
            task,
            username,
            filename,
            task_workdir,
            host_task_workdir,
        )

    return uploaded, filename


def upload_log_to_server(
    docker_client,
    container_name,
    task,
    username,
    filename,
    task_workdir,
    host_task_workdir,
):
    # dump docker logs to physical file on disk
    logger.debug("Dumping docker logs to file…")
    try:
        fpath = task_workdir / filename
        with ContainerLogsAsFile(docker_client, container_name) as infh, open(
            fpath, "wb"
        ) as outfh:
            while chunk := infh.read(8388608):  # 8 MiB
                outfh.write(chunk)
    except Exception as exc:
        logger.error(f"Unable to dump logs to {fpath}")
        logger.exception(exc)
        return False

    try:
        exit_code = -1
        logger.debug("Starting uploader container…")
        container = start_uploader(
            docker_client,
            task,
            "logs",
            username,
            host_workdir=host_task_workdir,
            upload_dir="",
            filename=filename,
            move=False,
            delete=False,
            compress=True,
            resume=True,
        )

        container.reload()
        # should log uploader above have been gone, we might expect this to fail
        # on super large mwoffliner with verbose mode on (20mn not enough for 20GB)
        exit_code = wait_container(docker_client, container.name, timeout=20 * 60)[
            "StatusCode"
        ]
    # connexion exception can be thrown by socket, urllib, requests
    except Exception as exc:
        logger.error(f"log upload could not complete. {exc}")
        stop_container(docker_client, container.name)
        exit_code = -1
    finally:
        logger.info(f"Scraper log upload complete: {exit_code}")

    if exit_code != 0:
        logger.error(
            f"Log Uploader:: " f"{get_container_logs(docker_client, container.name)}"
        )

    remove_container(docker_client, container.name, force=True)

    return exit_code == 0


def upload_log_to_s3(docker_client, container_name, upload_uri, key, delete_after):
    s3_storage = KiwixStorage(upload_uri)

    try:
        with ContainerLogsAsFile(docker_client, container_name) as fh:
            s3_storage.upload_fileobj(fileobj=fh, key=key, progress=True)
    except Exception as exc:
        logger.error(f"log upload failed: {exc}")
        logger.exception(exc)
        return False
    else:
        logger.info("uploaded log successfuly.")

    if delete_after is not None:
        try:
            # set expiration after bucket's min retention.
            # bucket retention is 1d minumum.
            # can be configured to lower value.
            # if expiration before bucket min retention, raises 400 Bad Request
            # on compliance
            expire_on = (
                datetime.datetime.now()
                + datetime.timedelta(days=delete_after or 1)
                # adding 1mn to prevent clash with bucket's equivalent min retention
                + datetime.timedelta(seconds=60)
            )
            logger.info(f"Setting autodelete to {expire_on}")
            s3_storage.set_object_autodelete_on(key=key, on=expire_on)
        except Exception as exc:
            logger.error(f"Failed to set log autodelete: {exc}")
            logger.exception(exc)
    return True
