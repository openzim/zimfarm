#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import os
import json
import logging

import zmq

from utils.json import Encoder

logger = logging.getLogger(__name__)


class MessageBroadcaster:
    def __init__(self, uri):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.uri = uri
        self.socket.bind(uri)

    def send(self, key, payload):
        try:
            self.socket.send_string(f"{key} {json.dumps(payload, cls=Encoder)}")
        except Exception as exc:
            logger.error(f"unable to brodcast on `{key}` with payload={payload}")
            logger.exception(exc)

    def broadcast_requested_task(self, task):
        self.send("requested-task", task)

    def broadcast_requested_tasks(self, tasks):
        self.send("requested-tasks", tasks)

    def broadcast_cancel_task(self, task):
        self.send("cancel-task", task)

    def broadcast_updated_task(self, task_id, event, payload={}):
        try:
            payload["_id"] = task_id
            payload["event"] = event
        except Exception:
            logger.error("received non-dict payload.")
            payload = {"_id": task_id, "event": event}
        self.send("task-event", payload)


BROADCASTER = MessageBroadcaster(os.getenv("SOCKET_URI", "tcp://localhost:5000"))
