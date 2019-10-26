#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import os

# worker names
WORKER_MANAGER = "worker-manager"
TASK_WORKER = "task-worker"

# task-related
CANCELLED = "cancelled"

# docker resources
DEFAULT_CPU_SHARE = 1024

# docker container names
CONTAINER_TASK_PREFIX = "zimtask_"
CONTAINER_SCRAPER_PREFIX = "zimscraper_"

# dispatcher-related
AUTH_EXPIRY = os.getenv("AUTH_EXPIRY", 60 * 59)  # seconds after which to re-auth
DEFAULT_WEB_API_URL = os.getenv("WEB_API_URI", "https://api.farm.openzim.org")
DEFAULT_SOCKET_URI = os.getenv("SOCKET_URI", "tcp://api.farm.openzim.org:5676")
ALL_OFFLINERS = ["mwoffliner", "youtube", "ted", "gutenberg"]
SUPPORTED_OFFLINERS = os.getenv("OFFLINERS", "").split() or ALL_OFFLINERS
