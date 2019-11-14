#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

""" zmq relay tester: listens to topic on relay's public channel """

import os
import logging

import zmq

SOCKET_URI = os.getenv("SOCKET_URI", "tcp://localhost:6000")
EVENTS = os.getenv("EVENTS", "requested-task,task-event").split(",")
logger = logging.getLogger("listener")

if not logger.hasHandlers():
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(asctime)s: %(levelname)s] %(message)s"))
    logger.addHandler(handler)


def main():
    context = zmq.Context()
    socket = context.socket(zmq.SUB)

    logger.info(f"connecting to {SOCKET_URI}…")
    socket.connect(SOCKET_URI)
    for event in EVENTS:
        logger.debug(f"subscribing to topic `{event}`")
        socket.setsockopt_string(zmq.SUBSCRIBE, event)

    while True:
        received_string = socket.recv_string()
        logger.info(f"[INCOMING] {received_string}")


if __name__ == "__main__":
    main()
