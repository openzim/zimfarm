#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import os
import pathlib
import multiprocessing

import psutil
import humanfriendly

from common import logger

# worker names
WORKER_MANAGER = "worker-manager"
TASK_WORKER = "task-worker"

# images
TASK_WORKER_IMAGE = os.getenv("TASK_WORKER_IMAGE", "openzim/task_worker:latest")

# paths
DEFAULT_WORKDIR = os.getenv("WORKDIR", "/data")  # in-container workdir for manager
DOCKER_SOCKET = docker_socket = pathlib.Path(
    os.getenv("DOCKER_SOCKET", "/var/run/docker.sock")
)
PRIVATE_KEY = docker_socket = pathlib.Path(
    os.getenv("PRIVATE_KEY", "/etc/ssh/keys/zimfarm")
)
OPENSSL_BIN = os.getenv("OPENSSL_BIN", "/usr/bin/openssl")

# task-related
CANCELED = "canceled"
CANCEL_REQUESTED = "cancel_requested"

# docker resources
DEFAULT_CPU_SHARE = 1024

# configuration
ZIMFARM_CPUS, ZIMFARM_MEMORY, ZIMFARM_DISK_SPACE = None, None, None

try:
    ZIMFARM_DISK_SPACE = humanfriendly.parse_size(os.getenv("ZIMFARM_DISK"))
except Exception as exc:
    ZIMFARM_DISK_SPACE = 2 ** 34  # 16GiB
    logger.error(
        f"Incorrect or missing `ZIMFARM_DISK` env. defaulting to {humanfriendly.format_size(ZIMFARM_DISK_SPACE, binary=True)} ({exc})"
    )

try:
    ZIMFARM_CPUS = int(os.getenv("ZIMFARM_CPUS"))
except Exception:
    physical_cpu = multiprocessing.cpu_count()
    if ZIMFARM_CPUS:
        ZIMFARM_CPUS = min([ZIMFARM_CPUS, physical_cpu])
    else:
        ZIMFARM_CPUS = physical_cpu

try:
    ZIMFARM_MEMORY = humanfriendly.parse_size(os.getenv("ZIMFARM_MEMORY"))
except Exception:
    physical_cpu = psutil.virtual_memory().total
    if ZIMFARM_MEMORY:
        ZIMFARM_MEMORY = min([ZIMFARM_MEMORY, physical_cpu])
    else:
        ZIMFARM_MEMORY = physical_cpu

USE_PUBLIC_DNS = bool(os.getenv("USE_PUBLIC_DNS", False))

# docker container names
CONTAINER_TASK_IDENT = "zimtask"
CONTAINER_SCRAPER_IDENT = "zimscraper"
CONTAINER_DNSCACHE_IDENT = "dnscache"

# dispatcher-related
AUTH_EXPIRY = os.getenv("AUTH_EXPIRY", 60 * 59)  # seconds after which to re-auth
DEFAULT_WEB_API_URL = os.getenv("WEB_API_URI", "https://api.farm.openzim.org")
DEFAULT_SOCKET_URI = os.getenv("SOCKET_URI", "tcp://api.farm.openzim.org:5000")
UPLOAD_URI = os.getenv("UPLOAD_URI", "sftp://warehouse.farm.openzim.org:1522")

OFFLINER_MWOFFLINER = "mwoffliner"
OFFLINER_YOUTUBE = "youtube"
OFFLINER_TED = "ted"
OFFLINER_PHET = "phet"
OFFLINER_GUTENBERG = "gutenberg"

ALL_OFFLINERS = [
    OFFLINER_MWOFFLINER,
    OFFLINER_YOUTUBE,
    OFFLINER_PHET,
    OFFLINER_GUTENBERG,
]
SUPPORTED_OFFLINERS = os.getenv("OFFLINERS", "").split() or ALL_OFFLINERS
