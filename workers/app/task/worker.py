#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import os
import time
import datetime
import pathlib

import humanfriendly

from common import logger
from common.worker import BaseWorker
from common.docker import query_container_stats

SLEEP_INTERVAL = 60  # nb of seconds to sleep before watching
ZIM_PATH = pathlib.Path(os.getenv("ZIM_PATH", "/zim-files"))


class Monitor:

    PENDING = "pending"
    UPLOADING = "uploading"
    FAILED_UPLOADING = "failed"
    UPLOADED = "uploaded"

    def __init__(self, task_id):
        self.task_id = task_id

        self.dnscache = None
        self.scraper = None
        self.upload = None

        self.files = []

    @property
    def scraper_alive(self):
        pass

    @property
    def is_working(self):
        return self.scraper_alive or self.is_uploading

    @property
    def is_uploading(self):
        pass

    def refresh_files_list(self):
        for fpath in ZIM_PATH.glob("*.zim"):
            if fpath.name not in self.files.keys():
                self.files.update({fpath.name: self.PENDING})

    def update(self):
        # update scraper
        self.scraper.reload()
        self.dnscache.reload()
        self.refresh_files_list()


class TaskWorker(BaseWorker):

    RUNNING = "running"

    def __init__(self, **kwargs):

        # print config
        self.print_config(**kwargs)

        # check workdir
        self.check_workdir()

        # ensure we have valid credentials
        self.check_auth()

        # ensure we have access to docker API
        self.check_docker()

        cont_stats = query_container_stats(self.workdir)
        logger.info(
            "Container resources:"
            "\n\tRAM  (total): {mem_total}"
            "\n\tRAM  (avail): {mem_avail}"
            "\n\tCPUs: {cpu_total}"
            "\n\tDisk: {disk_avail}".format(
                mem_total=humanfriendly.format_size(
                    cont_stats["memory"]["total"], binary=True
                ),
                mem_avail=humanfriendly.format_size(
                    cont_stats["memory"]["available"], binary=True
                ),
                cpu_total=cont_stats["cpu"]["total"],
                disk_avail=humanfriendly.format_size(
                    cont_stats["disk"]["available"], binary=True
                ),
            )
        )

        self._stop_requested = False

        self.dnscache = None  # dnscache container
        self.redis = None  # shared redis for the task

        self.zim_files = []

    def stop(self):
        # received TERM signal, gotta clean every thing up quick
        self._stop_requested = True

    def get_task(self):
        # self.task = get_task_detail(self.task_id)
        pass

    def start_dnscache(self):
        # self.dnscache = start_dnscache_container(self.task_id)
        pass

    def start_redis(self):
        # self.redis = start_redis_container(self.task_id)
        pass

    def setup_volume(self):
        pass

    def start_scraper(self):
        pass

    def list_and_upload_zim_files(self):
        pass

    def start_upload(self, fname):
        upload_uri = "sftp://url/{warehouse_path}/"

    def check_status(self):
        pass

    def immediate_shutdown(self):
        # PATCH url to set shutdown requested
        # docker kill for all running containers
        # scraper_log upload
        # clean-up volume
        pass

    def shutdown(self):
        # stop dnscache
        # clean-up volume
        pass

    def run(self):

        # get task detail from URL
        task = self.get_task()
        if task is None:
            logger.error("couldn't get task, exiting.")
            return

        # prepare folder
        self.setup_volume()

        # start our DNS cache
        self.start_dnscache()

        # start scraper
        self.start_scraper()

        last_check = datetime.datetime.now()

        while True:
            if self._stop_requested:
                self.immediate_shutdown()
                return

            now = datetime.datetime.now()
            if now - last_check.total_seconds() < SLEEP_INTERVAL:
                time.sleep(1)
                continue

            self.monitor.update()

            self.fetch_and_upload_scraper_log()

            self.list_and_upload_zim_files()

            if not self.monitor.working:
                break
            else:
                pass

        # done with processing, cleaning-up and exiting
        self.shutdown()
