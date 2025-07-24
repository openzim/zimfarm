import multiprocessing
import os
import re
from pathlib import Path
from typing import Any

import humanfriendly
import psutil

from zimfarm_worker.common.utils import as_pos_int


def getenv(key: str, *, mandatory: bool = False, default: Any = None) -> Any:
    value = os.getenv(key, default=default)

    if mandatory and not value:
        raise OSError(f"Please set the {key} environment variable")

    return value


DEBUG = getenv("DEBUG", default="false").lower() == "true"


# worker names
WORKER_MANAGER = "worker-manager"
TASK_WORKER = "task-worker"

# images
TASK_WORKER_IMAGE = getenv(
    "TASK_WORKER_IMAGE", default="ghcr.io/openzim/zimfarm-task-worker:latest"
)
DNSCACHE_IMAGE = getenv("DNSCACHE_IMAGE", default="ghcr.io/openzim/dnscache:latest")
UPLOADER_IMAGE = getenv("UPLOADER_IMAGE", default="ghcr.io/openzim/uploader:latest")
CHECKER_IMAGE = getenv("CHECKER_IMAGE", default="ghcr.io/openzim/zim-tools:3.5.0")
MONITOR_IMAGE = getenv(
    "MONITOR_IMAGE", default="ghcr.io/openzim/zimfarm-monitor:latest"
)

# paths
DEFAULT_WORKDIR = getenv("WORKDIR", default="/data")  # in-container workdir for manager
DOCKER_SOCKET = Path(getenv("DOCKER_SOCKET", default="/var/run/docker.sock"))
PRIVATE_KEY = Path(getenv("PRIVATE_KEY", default="/etc/ssh/keys/zimfarm"))
OPENSSL_BIN = getenv("OPENSSL_BIN", default="/usr/bin/openssl")

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
ZIMFARM_DISK_SPACE = as_pos_int(
    humanfriendly.parse_size(getenv("ZIMFARM_DISK", default=str(2**34)))
)

physical_cpu = multiprocessing.cpu_count()
zimfarm_cpus = as_pos_int(int(getenv("ZIMFARM_CPUS", default=physical_cpu)))
ZIMFARM_CPUS = min([zimfarm_cpus, physical_cpu])

zimfarm_task_cpus = getenv("ZIMFARM_TASK_CPUS", default="")
ZIMFARM_TASK_CPUS = float(zimfarm_task_cpus) if zimfarm_task_cpus else None

zimfarm_task_cpuset = getenv("ZIMFARM_TASK_CPUSET", default="")
if (
    not zimfarm_task_cpuset.isdigit()
    and not re.match(r"^\d+\-\d+$", zimfarm_task_cpuset)
    and not all(part.isdigit() for part in zimfarm_task_cpuset.split(","))
):
    zimfarm_task_cpuset = None

ZIMFARM_TASK_CPUSET = zimfarm_task_cpuset


physical_mem = psutil.virtual_memory().total
zimfarm_memory = as_pos_int(
    humanfriendly.parse_size(getenv("ZIMFARM_MEMORY", default=str(physical_mem)))
)
ZIMFARM_MEMORY = min([zimfarm_memory, physical_mem])

USE_PUBLIC_DNS = getenv("USE_PUBLIC_DNS", default="False").lower() == "true"
DISABLE_IPV6 = getenv("DISABLE_IPV6", default="False").lower() == "true"

# docker container names
CONTAINER_TASK_IDENT = "zimtask"
CONTAINER_SCRAPER_IDENT = "zimscraper"

# monitoring-related
MONITORING_DEST = getenv("MONITORING_DEST", default=None)  # {ip}:{port}
MONITORING_KEY = getenv("MONITORING_DEST", default=None)  # {uuid}

# dispatcher-related
DEFAULT_WEB_API_URLS = getenv(
    "WEB_API_URIS",
    default=getenv("WEB_API_URI", default="https://api.farm.openzim.org/v1"),
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
OFFLINER_DEVDOCS = "devdocs"
OFFLINER_MINDTOUCH = "mindtouch"

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
    OFFLINER_DEVDOCS,
    OFFLINER_MINDTOUCH,
]
# Get offliners from environment variable
offliners_env: str = getenv("OFFLINERS", default="")
offliners_list: list[str] = (
    list(filter(bool, offliners_env.split(","))) if offliners_env else ALL_OFFLINERS
)

SUPPORTED_OFFLINERS: list[str] = [
    offliner for offliner in offliners_list if offliner in ALL_OFFLINERS
]
PROGRESS_CAPABLE_OFFLINERS = [
    OFFLINER_ZIMIT,
    OFFLINER_SOTOKI,
    OFFLINER_IFIXIT,
    OFFLINER_YOUTUBE,
    OFFLINER_MINDTOUCH,
]

ALL_PLATFORMS = [
    "wikimedia",
    "youtube",
    "wikihow",
    "ifixit",
    "ted",
    "devdocs",
    "shamela",
    "libretexts",
    "phet",
]
PLATFORMS_TASKS: dict[str, int] = {}
for platform in ALL_PLATFORMS:
    name = f"PLATFORM_{platform}_MAX_TASKS"
    value = getenv(name, default=None)
    if not value:
        continue
    PLATFORMS_TASKS[platform] = int(value)

# number of times to retry a call to the Docker daemon
DOCKER_API_RETRIES = int(getenv("DOCKER_API_RETRIES", default=10))
DOCKER_API_RETRY_SECONDS = humanfriendly.parse_timespan(
    getenv("DOCKER_API_RETRY_DURATION", default="5s")
)
