#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import multiprocessing
import os
import pathlib
import re

import humanfriendly
import psutil

from common import logger
from common.utils import as_pos_int, format_size

# worker names
WORKER_MANAGER = "worker-manager"
TASK_WORKER = "task-worker"

# images
TASK_WORKER_IMAGE = (
    os.getenv("TASK_WORKER_IMAGE") or "ghcr.io/openzim/zimfarm-task-worker:latest"
)
DNSCACHE_IMAGE = os.getenv("DNSCACHE_IMAGE") or "ghcr.io/openzim/dnscache:latest"
UPLOADER_IMAGE = os.getenv("UPLOADER_IMAGE") or "ghcr.io/openzim/uploader:latest"
CHECKER_IMAGE = os.getenv("CHECKER_IMAGE") or "ghcr.io/openzim/zim-tools:3.4.2"
MONITOR_IMAGE = os.getenv("MONITOR_IMAGE") or "ghcr.io/openzim/zimfarm-monitor:latest"

# paths
DEFAULT_WORKDIR = os.getenv("WORKDIR", "/data")  # in-container workdir for manager
DOCKER_SOCKET = pathlib.Path(os.getenv("DOCKER_SOCKET", "/var/run/docker.sock"))
PRIVATE_KEY = pathlib.Path(os.getenv("PRIVATE_KEY", "/etc/ssh/keys/zimfarm"))
OPENSSL_BIN = os.getenv("OPENSSL_BIN", "/usr/bin/openssl")

# task-related
CANCELED = "canceled"
CANCEL_REQUESTED = "cancel_requested"
CANCELING = "canceling"

# connections related
access_token = "access_token"
refresh_token = "refresh_token"
token_payload = "token_payload"
authenticated_on = "authenticated_on"
authentication_expires_on = "authentication_expires_on"

# docker resources
DEFAULT_CPU_SHARE = 1024
DOCKER_CLIENT_TIMEOUT = 180  # 3mn for read timeout on docker API socket

# configuration
ZIMFARM_CPUS, ZIMFARM_MEMORY, ZIMFARM_DISK_SPACE = None, None, None

try:
    ZIMFARM_DISK_SPACE = as_pos_int(humanfriendly.parse_size(os.getenv("ZIMFARM_DISK")))
except Exception as exc:
    ZIMFARM_DISK_SPACE = 2**34  # 16GiB
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
    ZIMFARM_TASK_CPUS = float(os.getenv("ZIMFARM_TASK_CPUS"))
except Exception:
    ZIMFARM_TASK_CPUS = None

ZIMFARM_TASK_CPUSET = os.getenv("ZIMFARM_TASK_CPUSET", "")
if (
    not ZIMFARM_TASK_CPUSET.isdigit()
    and not re.match(r"^\d+\-\d+$", ZIMFARM_TASK_CPUSET)
    and not all([part.isdigit() for part in ZIMFARM_TASK_CPUSET.split(",")])
):
    ZIMFARM_TASK_CPUSET = None


try:
    ZIMFARM_MEMORY = as_pos_int(humanfriendly.parse_size(os.getenv("ZIMFARM_MEMORY")))
except Exception:
    physical_mem = psutil.virtual_memory().total
    if ZIMFARM_MEMORY:
        ZIMFARM_MEMORY = min([ZIMFARM_MEMORY, physical_mem])
    else:
        ZIMFARM_MEMORY = physical_mem

USE_PUBLIC_DNS = bool(os.getenv("USE_PUBLIC_DNS", False))
DISABLE_IPV6 = bool(os.getenv("DISABLE_IPV6", False))

# docker container names
CONTAINER_TASK_IDENT = "zimtask"
CONTAINER_SCRAPER_IDENT = "zimscraper"

# monitoring-related
MONITORING_DEST = os.getenv("MONITORING_DEST")  # {ip}:{port}
MONITORING_KEY = os.getenv("MONITORING_DEST")  # {uuid}

# dispatcher-related
DEFAULT_WEB_API_URLS = os.getenv(
    "WEB_API_URIS", os.getenv("WEB_API_URI", "https://api.farm.openzim.org/v1")
).split(",")
DEFAULT_WEB_API_URL = DEFAULT_WEB_API_URLS[0]  # used in task-worker's argparse default

OFFLINER_MWOFFLINER = "mwoffliner"
OFFLINER_YOUTUBE = "youtube"
OFFLINER_TED = "ted"
OFFLINER_OPENEDX = "openedx"
OFFLINER_PHET = "phet"
OFFLINER_GUTENBERG = "gutenberg"
OFFLINER_SOTOKI = "sotoki"
OFFLINER_NAUTILUS = "nautilus"
OFFLINER_ZIMIT = "zimit"
OFFLINER_KOLIBRI = "kolibri"
OFFLINER_WIKIHOW = "wikihow"
OFFLINER_IFIXIT = "ifixit"
OFFLINER_FREECODECAMP = "freecodecamp"

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
    OFFLINER_KOLIBRI,
    OFFLINER_WIKIHOW,
    OFFLINER_IFIXIT,
    OFFLINER_FREECODECAMP,
]
SUPPORTED_OFFLINERS = [
    offliner
    for offliner in (
        list(filter(bool, os.getenv("OFFLINERS", "").split(","))) or ALL_OFFLINERS
    )
    if offliner in ALL_OFFLINERS
]
PROGRESS_CAPABLE_OFFLINERS = [
    OFFLINER_ZIMIT,
    OFFLINER_SOTOKI,
    OFFLINER_IFIXIT,
    OFFLINER_YOUTUBE,
]

ALL_PLATFORMS = ["wikimedia", "youtube", "wikihow", "ifixit", "ted"]
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
