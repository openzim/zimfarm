#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import os
import pathlib
import multiprocessing

import psutil
import humanfriendly

from common import logger
from common.utils import as_pos_int, format_size

# worker names
WORKER_MANAGER = "worker-manager"
TASK_WORKER = "task-worker"

# images
TASK_WORKER_IMAGE = os.getenv("TASK_WORKER_IMAGE", "openzim/zimfarm-task-worker:latest")
DNSCACHE_IMAGE = os.getenv("DNSCACHE_IMAGE", "openzim/dnscache:1.0")
UPLOADER_IMAGE = os.getenv("UPLOADER_IMAGE", "openzim/uploader:1.0")

# paths
DEFAULT_WORKDIR = os.getenv("WORKDIR", "/data")  # in-container workdir for manager
DOCKER_SOCKET = pathlib.Path(os.getenv("DOCKER_SOCKET", "/var/run/docker.sock"))
PRIVATE_KEY = pathlib.Path(os.getenv("PRIVATE_KEY", "/etc/ssh/keys/zimfarm"))
OPENSSL_BIN = os.getenv("OPENSSL_BIN", "/usr/bin/openssl")

# task-related
CANCELED = "canceled"
CANCEL_REQUESTED = "cancel_requested"
CANCELING = "canceling"

# docker resources
DEFAULT_CPU_SHARE = 1024
DOCKER_CLIENT_TIMEOUT = 180  # 3mn for read timeout on docker API socket

# configuration
ZIMFARM_CPUS, ZIMFARM_MEMORY, ZIMFARM_DISK_SPACE = None, None, None

try:
    ZIMFARM_DISK_SPACE = as_pos_int(humanfriendly.parse_size(os.getenv("ZIMFARM_DISK")))
except Exception as exc:
    ZIMFARM_DISK_SPACE = 2 ** 34  # 16GiB
    logger.error(
        f"Incorrect or missing `ZIMFARM_DISK` env. "
        f"defaulting to {format_size(ZIMFARM_DISK_SPACE)} ({exc})"
    )

try:
    ZIMFARM_CPUS = as_pos_int(int(os.getenv("ZIMFARM_CPUS")))
except Exception:
    physical_cpu = multiprocessing.cpu_count()
    if ZIMFARM_CPUS:
        ZIMFARM_CPUS = min([ZIMFARM_CPUS, physical_cpu])
    else:
        ZIMFARM_CPUS = physical_cpu

try:
    ZIMFARM_MEMORY = as_pos_int(humanfriendly.parse_size(os.getenv("ZIMFARM_MEMORY")))
except Exception:
    physical_mem = psutil.virtual_memory().total
    if ZIMFARM_MEMORY:
        ZIMFARM_MEMORY = min([ZIMFARM_MEMORY, physical_mem])
    else:
        ZIMFARM_MEMORY = physical_mem

USE_PUBLIC_DNS = bool(os.getenv("USE_PUBLIC_DNS", False))

# docker container names
CONTAINER_TASK_IDENT = "zimtask"
CONTAINER_SCRAPER_IDENT = "zimscraper"
CONTAINER_DNSCACHE_IDENT = "dnscache"

# dispatcher-related
DEFAULT_WEB_API_URL = os.getenv("WEB_API_URI", "https://api.farm.openzim.org/v1")
DEFAULT_SOCKET_URI = os.getenv("SOCKET_URI", "tcp://api.farm.openzim.org:5000")

OFFLINER_MWOFFLINER = "mwoffliner"
OFFLINER_YOUTUBE = "youtube"
OFFLINER_TED = "ted"
OFFLINER_OPENEDX = "openedx"
OFFLINER_PHET = "phet"
OFFLINER_GUTENBERG = "gutenberg"
OFFLINER_SOTOKI = "sotoki"
OFFLINER_NAUTILUS = "nautilus"
OFFLINER_ZIMIT = "zimit"

ALL_OFFLINERS = [
    OFFLINER_MWOFFLINER,
    OFFLINER_YOUTUBE,
    OFFLINER_PHET,
    OFFLINER_GUTENBERG,
    OFFLINER_SOTOKI,
    OFFLINER_NAUTILUS,
    OFFLINER_TED,
    OFFLINER_OPENEDX,
    OFFLINER_ZIMIT,
]
SUPPORTED_OFFLINERS = [
    offliner
    for offliner in (
        list(filter(bool, os.getenv("OFFLINERS", "").split(","))) or ALL_OFFLINERS
    )
    if offliner in ALL_OFFLINERS
]

ALL_PLATFORMS = ["wikimedia", "youtube"]
PLATFORMS_TASKS = {}
for platform in ALL_PLATFORMS:
    name = f"PLATFORM_{platform}_MAX_TASKS"
    value = os.getenv(name)
    if not value:
        continue
    try:
        PLATFORMS_TASKS[platform] = int(value)
    except Exception:
        logger.debug(f"Incorrect value for {name} ({value}). Ignored.")
