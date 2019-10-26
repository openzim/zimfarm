#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import os
import json
import time
import signal
import datetime

import zmq
import requests
import humanfriendly

from common import logger
from common.worker import BaseWorker
from common.docker import query_host_stats
from common.constants import CANCELLED, SUPPORTED_OFFLINERS


class WorkerManager(BaseWorker):
    poll_interval = os.getenv("POLL_INTERVAL", 60)  # seconds between each manual poll
    sleep_interval = os.getenv("SLEEP_INTERVAL", 5)  # seconds to sleep while idle
    events = ["requested-task", "requested-tasks", "cancel-task"]
    config_keys = ["poll_interval", "sleep_interval", "events"]

    def __init__(self, **kwargs):
        # include our class config values in the config print
        kwargs.update({k: getattr(self, k) for k in self.config_keys})
        self.print_config(**kwargs)

        # set data holders
        self.tasks = {}
        self.last_poll = None
        self.should_stop = False

        # check workdir
        self.check_workdir()

        # ensure we have valid credentials
        self.check_auth()

        # ensure we have access to docker API
        self.check_docker()

        # display resources
        host_stats = query_host_stats(self.docker_api, self.workdir)
        logger.info(
            "Host hardware resources:"
            "\n\tCPU : {cpu_total} (total) ;  {cpu_avail} (avail)"
            "\n\tRAM : {mem_total} (total) ;  {mem_avail} (avail)"
            "\n\tDisk: {disk_avail} (avail)".format(
                mem_total=humanfriendly.format_size(
                    host_stats["memory"]["total"], binary=True
                ),
                mem_avail=humanfriendly.format_size(
                    host_stats["memory"]["available"], binary=True
                ),
                cpu_total=host_stats["cpu"]["total"],
                cpu_avail=host_stats["cpu"]["available"],
                disk_avail=humanfriendly.format_size(
                    host_stats["disk"]["available"], binary=True
                ),
            )
        )

        self.poll()

    @property
    def should_poll(self):
        return (
            datetime.datetime.now() - self.last_poll
        ).total_seconds() > self.poll_interval

    def sleep(self):
        time.sleep(self.sleep_interval)

    def poll(self, task_id=None):
        logger.info("manual polling…")
        self.last_poll = datetime.datetime.now()

        host_stats = query_host_stats(self.docker_api, self.workdir)
        matching = {
            "cpu": host_stats["cpu"]["available"],
            "memory": host_stats["memory"]["available"],
            "disk": host_stats["disk"]["available"],
            "offliners": SUPPORTED_OFFLINERS,
        }
        success, status_code, response = self.query_api(
            "GET",
            "/requested-tasks/",
            payload={"matching": matching},
            params={"limit": 2},
        )
        logger.info(f"polling result: {success}, HTTP {status_code}")
        logger.info(response)

    def check_cancellation(self):
        for task_id, task in self.tasks.items():
            if task["status"] == CANCELLED:
                continue  # already handling cancellation

            self.update_task_data(task_id)
            if task["status"] == CANCELLED:
                self.cancel_and_remove_task(task_id)

    def cancel_and_remove_task(self, task_id):
        self.stop_task_worker(task_id)
        self.tasks.pop(task_id, None)

    def update_task_data(self, task_id):
        """ request task object from server and update locally """
        success, status_code, response = self.query_api("GET", "/tasks/{task_id}")
        if success and status_code == requests.codes.OK:
            self.tasks[task_id] = response

        if status_code == requests.codes.NOT_FOUND:
            logger.warning(f"task is gone #{task_id}. cancelling it")
            self.cancel_and_remove_task(task_id)
        else:
            logger.warning(f"couldn't retrieve task detail for #{task_id}")

    def stop_task_worker(self, task_id):
        logger.debug(f"docker stop task_{task_id}")

    def handle_event(self, received_string):
        try:
            key, data = received_string.split(" ", 1)
            payload = json.loads(data)
            logger.info(f"received: {key} – {payload}")
        except Exception as exc:
            logger.exception(exc)
            logger.info(received_string)

    def exit_gracefully(self, signum, frame):
        signame = signal.strsignal(signum)
        logger.info(f"received exit signal ({signame}), stopping worker…")
        self.should_stop = True
        for task_id in self.tasks.keys():
            self.stop_task_worker(task_id)
        logger.info("clean-up successful")

    def run(self):
        context = zmq.Context()
        socket = context.socket(zmq.SUB)

        logger.info(f"subscribing to events from {self.socket_uri}…")
        socket.connect(self.socket_uri)
        for event in self.events:
            socket.setsockopt_string(zmq.SUBSCRIBE, event)

        logger.info("registering signals")

        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

        while not self.should_stop:
            try:
                received_string = socket.recv_string(zmq.DONTWAIT)
                self.handle_event(received_string)
            except zmq.Again:
                pass

            if self.should_poll:
                self.poll()
            else:
                self.sleep()
