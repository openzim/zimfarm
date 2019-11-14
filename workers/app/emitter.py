#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

""" zmq relay tester: emmit random messages to the `internal` channel """

import os
import time
import random
import logging

import zmq

SOCKET_URI = os.getenv("SOCKET_URI", "tcp://192.168.1.13:5000")
EVENTS = os.getenv("EVENTS", "requested-task,task-event").split(",")

logger = logging.getLogger("emitter")

if not logger.hasHandlers():
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(asctime)s: %(levelname)s] %(message)s"))
    logger.addHandler(handler)


def main():
    context = zmq.Context()
    socket = context.socket(zmq.PUB)

    logger.info(f"connecting to {SOCKET_URI}…")
    socket.connect(SOCKET_URI)

    while True:
        message = "{} {}".format(random.choice(EVENTS), random.randint(0, 1000))
        logger.info(f"[SENDING] {message}")
        socket.send_string(message)
        time.sleep(random.randint(5, 20))


if __name__ == "__main__":
    main()
