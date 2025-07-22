#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import collections
import datetime
import os
import signal
import time
import urllib.parse
from typing import Dict

import requests

from common import logger
from common.constants import (
    CANCEL_REQUESTED,
    CANCELED,
    CANCELING,
    PLATFORMS_TASKS,
    SUPPORTED_OFFLINERS,
)
from common.docker import (
    get_label_value,
    list_containers,
    query_host_stats,
    remove_container,
    start_task_worker,
    stop_task_worker,
)
from common.utils import as_pos_int, format_size
from common.worker import BaseWorker

TaskIdent = collections.namedtuple("TaskIdent", ["api_uri", "id"])


def ident_repr(self):
    return f"{self.id}@{self.api_uri.netloc}"


TaskIdent.__str__ = ident_repr


class WorkerManager(BaseWorker):
    poll_interval = int(os.getenv("POLL_INTERVAL", 180))  # seconds between each poll
    sleep_interval = int(os.getenv("SLEEP_INTERVAL", 5))  # seconds to sleep while idle
    selfish = bool(os.getenv("SELFISH", False))  # whether to only accept assigned tasks
    config_keys = ["poll_interval", "sleep_interval", "selfish"]

    def __init__(self, **kwargs):
        # include our class config values in the config print
        kwargs.update({k: getattr(self, k) for k in self.config_keys})
        kwargs.update({"OFFLINERS": SUPPORTED_OFFLINERS})
        kwargs.update({"PLATFORMS_TASKS": PLATFORMS_TASKS})
        self.print_config(**kwargs)

        # set data holders
        self.tasks: Dict[TaskIdent, Dict] = {}
        self.last_poll = datetime.datetime(2020, 1, 1)
        self.should_stop = False

        # check workdir
        self.check_workdir()

        # check SSH private key
        self.check_private_key()

        # ensure we have valid credentials
        self.check_auth()

        # ensure we have access to docker API
        self.check_docker()

        # display resources
        host_stats = query_host_stats(self.docker, self.workdir)

        logger.info(
            "Host hardware resources:"
            "\n\tCPU : {cpu_total} (total) ;  {cpu_avail} (avail)"
            "\n\tRAM : {mem_total} (total) ;  {mem_avail} (avail)"
            "\n\tDisk: {disk_total} (configured) ; {disk_avail} (avail) ; "
            "{disk_used} (reserved) ; {disk_remain} (remain)".format(
                mem_total=format_size(host_stats["memory"]["total"]),
                mem_avail=format_size(host_stats["memory"]["available"]),
                cpu_total=host_stats["cpu"]["total"],
                cpu_avail=host_stats["cpu"]["available"],
                disk_avail=format_size(host_stats["disk"]["available"]),
                disk_used=format_size(host_stats["disk"]["used"]),
                disk_remain=format_size(host_stats["disk"]["remaining"]),
                disk_total=format_size(host_stats["disk"]["total"]),
            )
        )

        if host_stats["disk"]["available"] < host_stats["disk"]["remaining"]:
            self.should_stop = True
            logger.critical("Configured disk space is not available. Exiting.")
            return

        self.check_in()

        # register stop/^C
        self.register_signals()

        self.sync_tasks_and_containers()

    @property
    def should_poll(self):
        return (
            datetime.datetime.now() - self.last_poll
        ).total_seconds() > self.poll_interval

    def sleep(self):
        time.sleep(self.sleep_interval)

    def get_next_webapi_uri(self) -> urllib.parse.ParseResult:
        """Next endpoint URI in line for polling

        Maintains an ordered iterator so each are called one after another"""

        def _get_iter():
            uris = [conn["uri"] for conn in self.connections.values()]
            index = 0
            while True:
                yield uris[index]
                index += 1
                if index >= len(uris):
                    index = 0

        if not hasattr(self, "uri_iter"):
            self.uri_iter = _get_iter()

        return next(self.uri_iter)

    def poll(self):
        self.check_cancellation()  # update our tasks register

        # a *poll* is *n* calls to our backend APIs
        for _ in range(len(self.connections)):
            # dont poll other APIs if we received a task. this will ensure the received
            # task gets to start and assign its resources before requesting more
            if self.poll_api(self.get_next_webapi_uri()):
                break

    def poll_api(self, webapi_uri) -> bool:
        logger.debug(f"polling {webapi_uri.netloc}…")
        self.last_poll = datetime.datetime.now()

        host_stats = query_host_stats(self.docker, self.workdir)
        expected_disk_avail = as_pos_int(
            host_stats["disk"]["total"] - host_stats["disk"]["used"]
        )
        if host_stats["disk"]["available"] < expected_disk_avail:
            self.should_stop = True
            logger.critical(
                f"Available disk space ({format_size(host_stats['disk']['available'])})"
                f" is lower than expected ({format_size(expected_disk_avail)}). Exiting"
            )
            return

        success, status_code, response = self.query_api(
            "GET",
            "/requested-tasks/worker",
            params={
                "worker": self.worker_name,
                "avail_cpu": host_stats["cpu"]["available"],
                "avail_memory": host_stats["memory"]["available"],
                "avail_disk": host_stats["disk"]["available"],
            },
            webapi_uri=webapi_uri.geturl(),
        )
        if not success:
            logger.warning(f"poll failed with HTTP {status_code}: {response}")
            return

        if self.selfish:
            response["items"] = [
                t for t in response["items"] if t["worker"] == self.worker_name
            ]

        if response["items"]:
            logger.info(
                "API is offering {nb} task(s): {ids}".format(
                    nb=len(response["items"]),
                    ids=[task["_id"] for task in response["items"]],
                )
            )
            self.start_task(response["items"].pop(), webapi_uri)
            # we need to allow the task to start, its container to start and
            # eventually its scraper to start so docker can report to us
            # the assigned resources (on the scraper) _before_ polling again
            self.last_poll = datetime.datetime.now() + datetime.timedelta(seconds=90)
            return True
        return False

    def check_in(self):
        """check_in_at() to all connections"""
        for connection in self.connections.values():
            self.check_in_at(connection["uri"])

    def check_in_at(self, webapi_uri: urllib.parse.ParseResult):
        """inform backend that we started a manager, sending resources info"""
        logger.info(f"checking-in with the API at {webapi_uri.netloc}…")

        host_stats = query_host_stats(self.docker, self.workdir)
        success, status_code, response = self.query_api(
            "PUT",
            f"/workers/{self.worker_name}/check-in",
            payload={
                "username": self.username,
                "selfish": self.selfish,
                "cpu": host_stats["cpu"]["total"],
                "memory": host_stats["memory"]["total"],
                "disk": host_stats["disk"]["total"],
                "offliners": SUPPORTED_OFFLINERS,
                "platforms": PLATFORMS_TASKS,
            },
            webapi_uri=webapi_uri.geturl(),
        )
        if not success:
            logger.error("\tunable to check-in with the API.")
            logger.debug(status_code)
            logger.debug(response)
            raise SystemExit()
        logger.info("\tchecked-in!")

    def check_cancellation(self):
        for task_ident in list(self.tasks.keys()):
            if self.tasks.get(task_ident, {}).get("status") in [CANCELED, CANCELING]:
                continue  # already handling cancellation

            self.update_task_data(task_ident)
            if self.tasks.get(task_ident, {}).get("status") in [
                CANCELED,
                CANCELING,
                CANCEL_REQUESTED,
            ]:
                self.cancel_and_remove_task(task_ident)

    def cancel_and_remove_task(self, task_ident: TaskIdent):
        logger.debug(f"canceling task: {task_ident}")
        try:
            self.tasks[task_ident]["status"] = CANCELING
        except KeyError:
            pass
        self.stop_task_worker(task_ident, timeout=60)
        self.tasks.pop(task_ident, None)

    def update_task_data(self, task_ident: TaskIdent):
        """request task object from server and update locally"""

        logger.debug(f"update_task_data: {task_ident}")
        success, status_code, response = self.query_api(
            "GET", f"/tasks/{task_ident.id}", webapi_uri=task_ident.api_uri.geturl()
        )
        if success and status_code == requests.codes.OK:
            self.tasks[task_ident] = response
            return True

        if status_code == requests.codes.NOT_FOUND:
            logger.warning(f"task {task_ident.id} is gone. cancelling it")
            self.cancel_and_remove_task(task_ident)
        else:
            logger.warning(f"couldn't retrieve task detail for {task_ident.id}")
        return success

    def sync_tasks_and_containers(self):
        # list of completed containers (successfuly ran)
        completed_containers = list_containers(
            self.docker, all=True, filters={"label": ["zimtask=yes"], "exited": 0}
        )

        # list of running containers
        running_containers = list_containers(
            self.docker, filters={"label": ["zimtask=yes"]}
        )

        # list of task_ids for running containers
        running_task_idents = [
            TaskIdent(
                urllib.parse.urlparse(
                    get_label_value(self.docker, container.name, "webapi_uri")
                ),
                get_label_value(self.docker, container.name, "task_id"),
            )
            for container in running_containers
        ]

        # remove completed containers
        for container in completed_containers:
            logger.info(f"container {container.name} exited successfuly, removing.")
            remove_container(self.docker, container.name)

        # make sure we are tracking task for all running containers
        for task_ident in running_task_idents:
            if task_ident not in self.tasks.keys():
                logger.info(f"found running container for {task_ident}.")
                self.update_task_data(task_ident)

        # filter our tasks register of gone containers
        for task_ident in list(self.tasks.keys()):
            if task_ident not in running_task_idents:
                logger.info(f"task {task_ident} is not running anymore, unwatching.")
                self.tasks.pop(task_ident, None)

    def stop_task_worker(self, task_ident: TaskIdent, timeout=20):
        logger.debug(f"stop_task_worker: {task_ident.id}")
        stop_task_worker(self.docker, task_ident.id, timeout=timeout)

    def start_task(self, requested_task: Dict, webapi_uri: urllib.parse.ParseResult):
        task_ident = TaskIdent(webapi_uri, requested_task["_id"])
        logger.debug(f"start_task: {task_ident}")

        success, status_code, response = self.query_api(
            "POST",
            f"/tasks/{task_ident.id}",
            params={"worker_name": self.worker_name},
            webapi_uri=task_ident.api_uri.geturl(),
        )
        if success and status_code == requests.codes.CREATED:
            self.update_task_data(task_ident)
            self.start_task_worker(requested_task, webapi_uri)
        elif status_code == requests.codes.LOCKED:
            logger.warning(f"task {task_ident.id} belongs to another worker. skipping")
        else:
            logger.warning(f"couldn't request task: {task_ident.id}")
            logger.warning(f"HTTP {status_code}: {response}")

    def start_task_worker(
        self, requested_task: Dict, webapi_uri: urllib.parse.ParseResult
    ):
        """launch docker task-worker container for task"""
        logger.debug(f"start_task_worker: {requested_task['_id']}")
        start_task_worker(
            self.docker,
            requested_task,
            webapi_uri.geturl(),
            self.username,
            self.workdir,
            self.worker_name,
        )

    def exit_gracefully(self, signum, frame):
        signame = signal.strsignal(signum)
        self.should_stop = True
        if signum == signal.SIGQUIT:
            logger.info(f"received exit signal ({signame}). stopping all task workers…")
            for task_ident in self.tasks.keys():
                self.stop_task_worker(task_ident)
        else:
            logger.info(f"received exit signal ({signame}).")
        logger.info("clean-up successful")

    def run(self):
        if self.should_stop:  # early exit
            return 1

        while not self.should_stop:
            if self.should_poll:
                self.sync_tasks_and_containers()
                self.poll()
            else:
                self.sleep()
