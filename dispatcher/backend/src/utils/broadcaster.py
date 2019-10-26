#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import json

import zmq

from utils.json import Encoder


class MessageBroadcaster:

    def __init__(self, ip_addr, port):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.address = f"{ip_addr}:{port}"
        self.socket.bind(f"tcp://{self.address}")

    def send(self, key, payload):
        self.socket.send_string(f"{key} {json.dumps(payload, cls=Encoder)}")

    def broadcast_requested_task(self, task):
        self.send("requested-task", task)

    def broadcast_requested_tasks(self, tasks):
        self.send("requested-tasks", tasks)

    def broadcast_cancel_task(self, task):
        self.send("cancel-task", task)


BROADCASTER = MessageBroadcaster(ip_addr="*", port=5676)
