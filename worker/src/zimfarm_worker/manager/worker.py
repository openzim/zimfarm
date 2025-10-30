#!/usr/bin/env python3
# vim: ai ts=4 sts=4 et sw=4 nu

import datetime
import signal
import time
import urllib.parse
from http import HTTPStatus
from pathlib import Path
from typing import Any, NamedTuple

from zimfarm_worker.common import getnow, logger
from zimfarm_worker.common.constants import (
    CANCEL_REQUESTED,
    CANCELED,
    CANCELING,
    CORDONED,
    PHYSICAL_CPU,
    PHYSICAL_MEMORY,
    PLATFORMS_TASKS,
    SUPPORTED_OFFLINERS,
    ZIMFARM_CPUS,
    ZIMFARM_MEMORY,
    getenv,
    parse_bool,
)
from zimfarm_worker.common.docker import (
    get_label_value,
    list_containers,
    query_host_stats,
    remove_container,
    start_task_worker,
    stop_task_worker,
)
from zimfarm_worker.common.utils import as_pos_int, format_size
from zimfarm_worker.common.worker import BaseWorker


class TaskIdent(NamedTuple):
    api_uri: str
    id: str


def ident_repr(self: TaskIdent):
    netloc = urllib.parse.urlparse(self.api_uri).netloc
    return f"{self.id}@{netloc}"


TaskIdent.__str__ = ident_repr


class WorkerManager(BaseWorker):
    poll_interval = int(
        getenv("POLL_INTERVAL", default=180)
    )  # seconds between each poll
    sleep_interval = int(
        getenv("SLEEP_INTERVAL", default=5)
    )  # seconds to sleep while idle
    selfish = parse_bool(
        getenv("SELFISH", default="false")
    )  # whether to only accept assigned tasks

    def __init__(
        self,
        username: str,
        webapi_uris: list[str],
        workdir: Path,
        worker_name: str,
    ):
        super().__init__(username, webapi_uris, workdir)
        self.worker_name = worker_name

        self.print_config(
            username=username,
            webapi_uris=webapi_uris,
            workdir=workdir,
            worker_name=worker_name,
            OFFLINERS=SUPPORTED_OFFLINERS,
            PLATFORMS_TASKS=PLATFORMS_TASKS,
            poll_interval=self.poll_interval,
            sleep_interval=self.sleep_interval,
            selfish=self.selfish,
        )
        if ZIMFARM_MEMORY > PHYSICAL_MEMORY:
            logger.warning(
                f"Declared memory {ZIMFARM_MEMORY} appears to be greater than actual "
                f"memory {PHYSICAL_MEMORY}"
            )

        if ZIMFARM_CPUS > PHYSICAL_CPU:
            logger.warning(
                f"Declared CPU count {ZIMFARM_CPUS} appears to be greater than actual "
                f"CPU count {PHYSICAL_CPU}"
            )

        # set data holders
        self.tasks: dict[TaskIdent, dict[str, Any]] = {}
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
            f"\n\tCPU : {host_stats.cpu.total} (total) ;  {host_stats.cpu.available} "
            "(avail)"
            f"\n\tRAM : {format_size(host_stats.memory.total)} (total) ;  "
            f"{format_size(host_stats.memory.available)} (avail)"
            f"\n\tDisk: {format_size(host_stats.disk.total)} (configured) ; "
            f"{format_size(host_stats.disk.available)} (avail) ; "
            f"{format_size(host_stats.disk.used)} (reserved) ; "
            f"{format_size(host_stats.disk.remaining)} (remaining)"
        )

        if host_stats.disk.available < host_stats.disk.remaining:
            self.should_stop = True
            logger.critical("Configured disk space is not available. Exiting.")
            return

        self.check_in()

        # register stop/^C
        self.register_signals()

        self.sync_tasks_and_containers()

    @property
    def should_poll(self):
        return (getnow() - self.last_poll).total_seconds() > self.poll_interval

    def sleep(self):
        time.sleep(self.sleep_interval)

    def get_next_webapi_uri(self) -> str:
        """Next endpoint URI in line for polling

        Maintains an ordered iterator so each are called one after another"""

        def _get_iter():
            uris = [conn.uri for conn in self.connections.values()]
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

    def poll_api(self, webapi_uri: str) -> bool:
        logger.debug(f"polling {webapi_uri}…")
        self.last_poll = getnow()

        host_stats = query_host_stats(self.docker, self.workdir)
        expected_disk_avail = as_pos_int(host_stats.disk.total - host_stats.disk.used)
        if host_stats.disk.available < expected_disk_avail:
            self.should_stop = True
            logger.critical(
                f"Available disk space ({format_size(host_stats.disk.available)})"
                f" is lower than expected ({format_size(expected_disk_avail)}). Exiting"
            )
            return False

        response = self.query_api(
            method="GET",
            path="/requested-tasks/worker",
            params={
                "worker_name": self.worker_name,
                "avail_cpu": host_stats.cpu.available,
                "avail_memory": host_stats.memory.available,
                "avail_disk": host_stats.disk.available,
            },
            webapi_uri=webapi_uri,
        )
        if not response.success:
            logger.warning(
                f"poll failed with HTTP {response.status_code}: {response.json}"
            )
            return False

        if self.selfish:
            response.json["items"] = [
                t
                for t in response.json["items"]
                if t["worker_name"] == self.worker_name
            ]

        if response.json["items"]:
            logger.info(
                "API is offering {nb} task(s): {ids}".format(
                    nb=len(response.json["items"]),
                    ids=[task["id"] for task in response.json["items"]],
                )
            )
            self.start_task(response.json["items"].pop(), webapi_uri)
            # we need to allow the task to start, its container to start and
            # eventually its scraper to start so docker can report to us
            # the assigned resources (on the scraper) _before_ polling again
            self.last_poll = getnow() + datetime.timedelta(seconds=90)
            return True
        return False

    def check_in(self):
        """check_in_at() to all connections"""
        for connection in self.connections.values():
            self.check_in_at(connection.uri)

    def check_in_at(self, webapi_uri: str):
        """inform backend that we started a manager, sending resources info"""
        netloc = urllib.parse.urlparse(webapi_uri).netloc
        logger.info(f"checking-in with the API at {netloc}…")

        host_stats = query_host_stats(self.docker, self.workdir)
        response = self.query_api(
            method="PUT",
            path=f"/workers/{self.worker_name}/check-in",
            payload={
                "username": self.username,
                "selfish": self.selfish,
                "cpu": host_stats.cpu.total,
                "memory": host_stats.memory.total,
                "disk": host_stats.disk.total,
                "offliners": SUPPORTED_OFFLINERS,
                "platforms": PLATFORMS_TASKS,
                "cordoned": CORDONED,
            },
            webapi_uri=webapi_uri,
        )
        if not response.success:
            logger.error("\tunable to check-in with the API.")
            logger.debug(response.status_code)
            logger.debug(response.json)
            raise SystemExit()
        logger.info("\tchecked-in!")

    def check_cancellation(self):
        for task_ident in list(self.tasks.keys()):
            if self.tasks.get(task_ident, {}).get("status") in [CANCELED, CANCELING]:
                continue  # already handling cancellation

            self.update_task_data(task_ident)
            logger.debug(f"Checking if task {task_ident} should be cancelled...")
            event_codes = {
                event["code"]
                for event in self.tasks.get(task_ident, {}).get("events", [])
            }
            cancel_events = {CANCEL_REQUESTED, CANCELED}
            if (
                self.tasks.get(task_ident, {}).get("status") in cancel_events
                or event_codes & cancel_events
            ):
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
        response = self.query_api(
            method="GET",
            path=f"/tasks/{task_ident.id}",
            webapi_uri=task_ident.api_uri,
        )
        if response.success and response.status_code == HTTPStatus.OK:
            self.tasks[task_ident] = response.json
            return True

        if response.status_code == HTTPStatus.NOT_FOUND:
            logger.warning(f"task {task_ident.id} is gone. cancelling it")
            self.cancel_and_remove_task(task_ident)
        else:
            logger.warning(f"couldn't retrieve task detail for {task_ident.id}")
        return response.success

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
                get_label_value(self.docker, container.name, "webapi_uri"),
                get_label_value(self.docker, container.name, "task_id"),
            )
            for container in running_containers
        ]

        # remove completed containers
        for container in completed_containers:
            logger.info(f"container {container.name} exited successfuly, removing.")
            remove_container(self.docker, container=container.name)

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

    def stop_task_worker(self, task_ident: TaskIdent, timeout: int = 20):
        logger.debug(f"stop_task_worker: {task_ident.id}")
        stop_task_worker(self.docker, task_id=task_ident.id, timeout=timeout)

    def start_task(self, requested_task: dict[str, Any], webapi_uri: str):
        task_ident = TaskIdent(webapi_uri, requested_task["id"])
        logger.debug(f"start_task: {task_ident}")

        response = self.query_api(
            method="POST",
            path=f"/tasks/{task_ident.id}",
            payload={"worker_name": self.worker_name},
            webapi_uri=task_ident.api_uri,
        )
        if response.success and response.status_code == HTTPStatus.CREATED:
            self.update_task_data(task_ident)
            self.start_task_worker(requested_task, webapi_uri)
        elif response.status_code == HTTPStatus.LOCKED:
            logger.warning(f"task {task_ident.id} belongs to another worker. skipping")
        else:
            logger.warning(f"couldn't request task: {task_ident.id}")
            logger.warning(f"HTTP {response.status_code}: {response.json}")

    def start_task_worker(self, requested_task: dict[str, Any], webapi_uri: str):
        """launch docker task-worker container for task"""
        logger.debug(f"start_task_worker: {requested_task['id']}")
        start_task_worker(
            self.docker,
            task=requested_task,
            webapi_uri=webapi_uri,
            username=self.username,
            workdir=self.workdir,
            worker_name=self.worker_name,
        )

    def exit_gracefully(self, signum: int, _: Any):
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
