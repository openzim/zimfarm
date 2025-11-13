# pyright: strict, reportUnknownParameterType=false
import os
import re
import time
import urllib.parse
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
from pathlib import Path
from typing import Any, Literal

from docker import DockerClient
from docker.errors import APIError, ImageNotFound, NotFound
from docker.models.containers import Container
from docker.models.images import Image
from docker.types import Mount

from zimfarm_worker.common import logger
from zimfarm_worker.common.constants import (
    CHECKER_IMAGE,
    CONTAINER_SCRAPER_IDENT,
    CONTAINER_TASK_IDENT,
    DEFAULT_CPU_SHARE,
    DISABLE_IPV6,
    DNSCACHE_IMAGE,
    DOCKER_API_RETRIES,
    DOCKER_API_RETRY_SECONDS,
    DOCKER_SOCKET,
    ENVIRONMENT,
    MONITOR_IMAGE,
    MONITORING_DEST,
    MONITORING_KEY,
    PRIVATE_KEY,
    TASK_WORKER_IMAGE,
    UPLOADER_IMAGE,
    USE_PUBLIC_DNS,
    ZIMFARM_CPUS,
    ZIMFARM_DISK_SPACE,
    ZIMFARM_MEMORY,
    ZIMFARM_TASK_CPUS,
    ZIMFARM_TASK_CPUSET,
)
from zimfarm_worker.common.utils import as_pos_int, format_size, short_id

RUNNING_STATUSES = ("created", "running", "restarting", "paused", "removing")
STOPPED_STATUSES = ("exited", "dead")
RESOURCES_DISK_LABEL = "resources_disk"


def retry(
    func: Callable[..., Any] | None = None,
    *,
    retries: int = DOCKER_API_RETRIES,
    interval: float = DOCKER_API_RETRY_SECONDS,
) -> Any:
    """Retry API calls to the Docker daemon on failure."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapped(*args: Any, **kwargs: Any):
            attempt = 0
            while True:
                attempt += 1
                try:
                    return func(*args, **kwargs)
                # most 404 errors would be from incorrect image/tag name but
                # we still want to avoid crashing on 404 due to temporary
                # docker-hub issues
                except (ImageNotFound, APIError) as exc:
                    if attempt <= retries and exc.is_server_error():
                        logger.error(
                            f"docker api error for {func.__name__} "
                            f"(attempt {attempt}): {exc}"
                        )
                        time.sleep(interval * attempt)
                        continue
                    raise exc

        return wrapped

    if func:
        return decorator(func)

    return decorator


@retry
def get_image(client: DockerClient, name: str):
    return client.images.get(name)


@retry
def pull_image(client: DockerClient, repository: str, tag: str | None = None):
    return client.images.pull(repository, tag)


@retry
def run_container(client: DockerClient, image: Image, **kwargs: Any) -> Container:
    return client.containers.run(
        image, **kwargs
    )  # pyright: ignore[reportGeneralTypeIssues, reportReturnType, reportUnknownVariableType]


@retry
def get_container(client: DockerClient, container_name: str) -> Container:
    container = client.containers.get(container_name)
    container.reload()
    return container  # pyright: ignore [reportGeneralTypeIssues,reportReturnType]


@retry
def list_containers(client: DockerClient, **kwargs: Any):
    """all=False, since="Id or name", before="Id or name", limit=None, filters={}"""
    return client.containers.list(  # pyright: ignore[reportGeneralTypeIssues, reportReturnType, reportUnknownMemberType, reportUnknownVariableType]
        **kwargs
    )


@retry
def remove_container(client: DockerClient, **kwargs: Any):
    """container="", v=False, link=False, force=False"""
    return client.api.remove_container(
        **kwargs
    )  # pyright: ignore[reportGeneralTypeIssues, reportReturnType]


@retry
def prune_containers(client: DockerClient, **kwargs: Any):
    """filters={}"""
    return client.api.prune_containers(  # pyright: ignore[reportGeneralTypeIssues, reportUnknownMemberType, reportUnknownVariableType]
        **kwargs
    )


@retry
def stop_container(client: DockerClient, container: str, **kwargs: Any):
    """container="", timeout=None"""
    return client.api.stop(
        container, **kwargs
    )  # pyright: ignore[reportGeneralTypeIssues, reportReturnType]


@retry
def wait_container(client: DockerClient, **kwargs: Any):
    """container="", timeout=None, condition="" """
    return client.api.wait(**kwargs)


@retry
def container_logs(client: DockerClient, **kwargs: Any):
    """container, stdout=True, stderr=True, stream=False, timestamps=False,
    tail='all', since=None, follow=None, until=None"""
    return client.api.logs(
        **kwargs
    )  # pyright: ignore[reportGeneralTypeIssues, reportReturnType, reportUnknownVariableType]


@retry
def get_or_pull_image(client: DockerClient, name: str):
    """attempt to get locally or pull and return. Name is repo:tag"""
    if ":" not in name:
        # consider missing :tag info as a local image for tests
        return client.images.get(
            name
        )  # pyright: ignore[reportGeneralTypeIssues,reportReturnType]

    return client.images.pull(
        name
    )  # pyright: ignore[reportGeneralTypeIssues,reportReturnType]


@dataclass(kw_only=True)
class ContainerResources:
    cpu_shares: int
    memory: int
    disk: int


def query_containers_resources(client: DockerClient):
    cpu_shares = 0
    memory = 0
    disk = 0
    for container in list_containers(client, filters={"name": CONTAINER_SCRAPER_IDENT}):
        container.reload()
        cpu_shares += container.attrs["HostConfig"]["CpuShares"] or DEFAULT_CPU_SHARE
        memory += container.attrs["HostConfig"]["Memory"]

    for container in list_containers(client, filters={"name": CONTAINER_TASK_IDENT}):
        try:
            disk += int(container.labels.get(RESOURCES_DISK_LABEL, 0))
        except Exception:
            disk += 0  # improper label

    return ContainerResources(cpu_shares=cpu_shares, memory=memory, disk=disk)


@dataclass(kw_only=True)
class ResourceStats:
    total: int = 0
    used: int = 0
    available: int = 0


@dataclass(kw_only=True)
class ResourceStatsWithRemaining(ResourceStats):
    remaining: int = 0


@dataclass(kw_only=True)
class HostStats:
    cpu: ResourceStats
    disk: ResourceStatsWithRemaining
    memory: ResourceStatsWithRemaining


def query_host_stats(client: DockerClient, workdir: Path):
    # query cpu and ram usage in our containers
    stats = query_containers_resources(client)

    # disk space
    workir_fs_stats = os.statvfs(workdir)
    disk_used = stats.disk
    disk_free = workir_fs_stats.f_bavail * workir_fs_stats.f_frsize

    # CPU cores
    cpu_used = stats.cpu_shares // DEFAULT_CPU_SHARE
    cpu_avail = as_pos_int(ZIMFARM_CPUS - cpu_used)

    # RAM
    mem_used = stats.memory
    mem_avail = as_pos_int(ZIMFARM_MEMORY - mem_used)

    return HostStats(
        cpu=ResourceStats(total=ZIMFARM_CPUS, used=cpu_used, available=cpu_avail),
        disk=ResourceStatsWithRemaining(
            total=ZIMFARM_DISK_SPACE,
            used=disk_used,
            available=disk_free,
            remaining=ZIMFARM_DISK_SPACE - disk_used,
        ),
        memory=ResourceStatsWithRemaining(
            total=ZIMFARM_MEMORY,
            used=mem_used,
            available=mem_avail,
            remaining=ZIMFARM_MEMORY - mem_used,
        ),
    )


@dataclass(kw_only=True)
class ContainerStats:
    cpu: ResourceStats
    disk: ResourceStats
    memory: ResourceStats


def query_container_stats(workdir: str):
    workir_fs_stats = os.statvfs(workdir)
    avail_disk = workir_fs_stats.f_bavail * workir_fs_stats.f_frsize

    # dockerd < 20 /sys structure
    if Path("/sys/fs/cgroup/memory/memory.limit_in_bytes").exists():
        with open("/sys/fs/cgroup/memory/memory.limit_in_bytes") as fp:
            mem_total = int(fp.read().strip())
        with open("/sys/fs/cgroup/memory/memory.usage_in_bytes") as fp:
            mem_used = int(fp.read().strip())
        with open("/sys/fs/cgroup/cpuacct/cpuacct.usage_percpu") as fp:
            cpu_total = len(fp.read().strip().split())
    # dockerd >= 20 /sys structure
    else:
        with open("/sys/fs/cgroup/memory.max") as fp:
            mem_total = int(fp.read().strip())
        with open("/sys/fs/cgroup/memory.current") as fp:
            mem_used = int(fp.read().strip())
        with open("/sys/fs/cgroup/cpuset.cpus.effective") as fp:
            cpu_total = int(fp.read().strip().split("-", 1)[-1])

    mem_avail = mem_total - mem_used
    return ContainerStats(
        cpu=ResourceStats(total=cpu_total),
        disk=ResourceStats(available=avail_disk),
        memory=ResourceStats(total=mem_total, available=mem_avail),
    )


def get_running_container_name() -> str:
    """Determine the name of this container."""
    return (Path("/etc/hostname").read_text()).strip()


def query_host_mounts(
    client: DockerClient, keys: list[Path] | None = None
) -> dict[Path, Path]:
    if keys is None:
        keys = []
    return query_container_mounts(
        client, get_running_container_name(), [DOCKER_SOCKET, PRIVATE_KEY, *keys]
    )


def query_container_mounts(
    client: DockerClient, container_name: str, keys: list[Path]
) -> dict[Path, Path]:
    container = get_container(client, container_name)
    mounts: dict[Path, Path] = {}
    for mount in container.attrs["Mounts"]:
        dest = Path(mount["Destination"])
        if dest in keys:
            key = keys[keys.index(dest)]
            mounts[key] = Path(mount["Source"])
    return mounts


def get_container_name(kind: str, task_id: str) -> str:
    return f"{kind}_{short_id(task_id)}"


def get_scraper_container_name(offliner: str, task_id: str) -> str:
    return get_container_name(f"{CONTAINER_SCRAPER_IDENT}_{offliner}", task_id)


def upload_container_name(
    task_id: str, filename: str, kind: str, *, unique: bool
) -> str:
    if unique:
        filename = f"{uuid.uuid4().hex}{Path(filename).suffix}"
    else:
        filename = re.sub(r"[^a-zA-Z0-9_.-]", "_", filename)
    return f"{short_id(task_id)}_{kind}up_{filename}"


def get_ip_address(client: DockerClient, name: str) -> str:
    """IP Address (first) of a named container"""
    return get_container(client, name).attrs["NetworkSettings"]["IPAddress"]


def get_label_value(client: DockerClient, name: str, label: str) -> str:
    """direct access to a single label value"""
    return get_container(client, name).attrs["Config"]["Labels"].get(label)


def get_sysctl():
    return {"net.ipv6.conf.all.disable_ipv6": "1"} if DISABLE_IPV6 else None


def start_dnscache(client: DockerClient, task: dict[str, Any]) -> Container:
    name = get_container_name("dnscache", task["id"])
    environment = {"USE_PUBLIC_DNS": "yes" if USE_PUBLIC_DNS else "no"}
    image = get_or_pull_image(client, DNSCACHE_IMAGE)
    return run_container(
        client,
        image=image,
        detach=True,
        name=name,
        environment=environment,
        remove=False,
        labels={
            "zimfarm": "",
            "task_id": task["id"],
            "tid": short_id(task["id"]),
            "schedule_name": task["schedule_name"],
        },
        sysctls=get_sysctl(),
    )


def start_monitor(
    client: DockerClient,
    *,
    task: dict[str, Any],
    monitoring_key: str,
):
    name = get_container_name("monitor", task["id"])
    image = get_or_pull_image(client, MONITOR_IMAGE)

    host_mounts = query_host_mounts(client, [DOCKER_SOCKET])
    host_docker_socket = str(host_mounts.get(DOCKER_SOCKET))

    mounts = [
        Mount("/host/etc/passwd", "/etc/passwd", type="bind", read_only=True),
        Mount("/host/etc/group", "/etc/group", type="bind", read_only=True),
        Mount("/host/proc", "/proc", type="bind", read_only=True),
        Mount("/host/sys", "/sys", type="bind", read_only=True),
        Mount("/host/etc/os-release", "/etc/os-release", type="bind", read_only=True),
        Mount("/var/run/docker.sock", host_docker_socket, type="bind", read_only=True),
    ]

    environment = {
        "SCRAPER_CONTAINER": get_ip_address(
            client,
            get_scraper_container_name(
                offliner=task["config"]["offliner"]["offliner_id"], task_id=task["id"]
            ),
        ),
        "NETDATA_HOSTNAME": "{task_ident}.{worker}".format(
            task_ident=get_container_name(task["schedule_name"], task["id"]),
            worker=task["worker_name"],
        ),
    }
    if MONITORING_DEST:
        environment["MONITORING_DEST"] = MONITORING_DEST
    if monitoring_key:
        environment["MONITORING_KEY"] = monitoring_key

    return run_container(
        client,
        image=image,
        detach=True,
        name=name,
        mounts=mounts,
        remove=False,
        labels={
            "zimfarm": "",
            "task_id": task["id"],
            "tid": short_id(task["id"]),
            "schedule_name": task["schedule_name"],
        },
        environment=environment,
        cap_add=["SYS_PTRACE"],
        security_opt=["apparmor=unconfined"],
        sysctls=get_sysctl(),
    )


def start_checker(
    client: DockerClient, *, task: dict[str, Any], host_workdir: Path, filename: str
):
    name = get_container_name("checker", task["id"])
    image = get_or_pull_image(client, CHECKER_IMAGE)

    # remove container should it exists (should not)
    try:
        remove_container(client, container=name)
        prune_containers(client, {"label": [f"filename={filename}"]})
    except NotFound:
        pass

    # in container paths
    workdir = Path("/data")
    filepath = workdir.joinpath(filename)
    mounts = [Mount(str(workdir), str(host_workdir), type="bind", read_only=True)]

    command: list[str] = [
        "zimcheck",
        "--json",
        task["upload"]["zim"]["zimcheck"] or "--all",
        str(filepath),
    ]

    return run_container(
        client,
        image=image,
        command=command,
        detach=True,
        name=name,
        mounts=mounts,
        labels={
            "zimfarm": "",
            "task_id": task["id"],
            "tid": short_id(task["id"]),
            "schedule_name": task["schedule_name"],
            "filename": filename,
        },
        remove=False,
        sysctls=get_sysctl(),
    )


def start_scraper(
    client: DockerClient,
    *,
    task: dict[str, Any],
    dns: list[str] | None,
    host_workdir: Path,
):
    config = task["config"]
    container_name = get_scraper_container_name(
        offliner=config["offliner"]["offliner_id"], task_id=task["id"]
    )

    # remove container should it exists (should not)
    try:
        remove_container(client, container=container_name)
    except NotFound:
        pass

    # scraper is systematically pulled before starting
    name = f"{config['image']['name']}:{config['image']['tag']}"
    logger.debug(f"Pulling image {name}")
    docker_image = pull_image(client, name)

    # where to mount volume inside scraper
    mount_point = config["mount_point"]

    # mounts will be attached to host's fs, not this one
    mounts = [Mount(str(mount_point), str(host_workdir), type="bind")]

    command = config["str_command"]
    cpu_shares = config["resources"]["cpu"] * DEFAULT_CPU_SHARE
    mem_limit = config["resources"]["memory"]
    disk_limit = config["resources"]["disk"]
    shm_size = config["resources"].get("shm")
    cap_add = config["resources"].get("cap_add", [])
    cap_drop = config["resources"].get("cap_drop", [])

    if ZIMFARM_TASK_CPUS:
        period = 100000
        quota = int(period * ZIMFARM_TASK_CPUS)
    else:
        period = quota = None

    kwargs = {
        "image": docker_image,
        "command": command,
        # disk is already reserved on zimtask
        "cpu_shares": cpu_shares,
        "cpu_period": period,
        "cpu_quota": quota,
        "cpuset_cpus": ZIMFARM_TASK_CPUSET or None,
        "mem_limit": mem_limit,
        "detach": True,
        "labels": {
            "zimfarm": "",
            "zimscraper": "yes",
            "task_id": task["id"],
            "tid": short_id(task["id"]),
            "schedule_name": task["schedule_name"],
            "human.cpu": str(config["resources"]["cpu"]),
            "human.memory": format_size(mem_limit),
            "human.disk": format_size(disk_limit),
            "human.task-cpu": str(ZIMFARM_TASK_CPUS),
            "human.task-cpuset": str(ZIMFARM_TASK_CPUSET),
        },
        "mem_swappiness": 0,
        "shm_size": shm_size,
        "cap_add": cap_add,
        "cap_drop": cap_drop,
        "mounts": mounts,
        "name": container_name,
        "remove": False,  # scraper container will be removed once log&zim handled
        "sysctls": get_sysctl(),
    }
    if dns:
        kwargs["dns"] = dns

    if ENVIRONMENT == "development":
        kwargs["network_mode"] = f"container:{get_running_container_name()}"

    return run_container(
        client,
        **kwargs,
    )


def start_task_worker(
    client: DockerClient,
    *,
    task: dict[str, Any],
    webapi_uri: str,
    username: str,
    workdir: Path,
    worker_name: str,
):
    container_name = get_container_name(CONTAINER_TASK_IDENT, task["id"])

    # remove container should it exists (should not)
    try:
        remove_container(client, container=container_name)
    except NotFound:
        pass

    logger.debug(f"getting image {TASK_WORKER_IMAGE}")
    # task worker is always pulled to ensure we can update our code
    if ":" not in TASK_WORKER_IMAGE:
        # consider missing :tag info as a local image for tests
        docker_image = get_image(client, TASK_WORKER_IMAGE)
    else:
        docker_image = pull_image(client, TASK_WORKER_IMAGE)

    host_mounts = query_host_mounts(client, [workdir])
    host_task_workdir = str(host_mounts.get(workdir))
    host_docker_socket = str(host_mounts.get(DOCKER_SOCKET))
    host_private_key = str(host_mounts.get(PRIVATE_KEY))
    # mounts will be attached to host's fs, not this one
    mounts = [
        Mount(str(workdir), host_task_workdir, type="bind"),
        Mount(str(DOCKER_SOCKET), host_docker_socket, type="bind", read_only=True),
        Mount(str(PRIVATE_KEY), host_private_key, type="bind", read_only=True),
    ]
    command = ["task-worker", "--task-id", task["id"], "--webapi-uri", webapi_uri]

    logger.debug(f"running {command}")
    return run_container(
        client,
        image=docker_image,
        command=command,
        detach=True,
        environment={
            "USERNAME": username,
            "WORKDIR": str(workdir),
            "WEB_API_URI": webapi_uri,
            "WORKER_NAME": worker_name,
            "ZIMFARM_DISK": os.getenv("ZIMFARM_DISK"),
            "ZIMFARM_CPUS": os.getenv("ZIMFARM_CPUS"),
            "ZIMFARM_TASK_CPUS": os.getenv("ZIMFARM_TASK_CPUS"),
            "ZIMFARM_TASK_CPUSET": os.getenv("ZIMFARM_TASK_CPUSET"),
            "ZIMFARM_MEMORY": os.getenv("ZIMFARM_MEMORY"),
            "DEBUG": os.getenv("DEBUG"),
            "ENVIRONMENT": ENVIRONMENT,
            "USE_PUBLIC_DNS": "yes" if USE_PUBLIC_DNS else "",
            "DISABLE_IPV6": "yes" if DISABLE_IPV6 else "",
            "UPLOADER_IMAGE": UPLOADER_IMAGE,
            "CHECKER_IMAGE": CHECKER_IMAGE,
            "DNSCACHE_IMAGE": DNSCACHE_IMAGE,
            "MONITOR_IMAGE": MONITOR_IMAGE,
            "MONITORING_DEST": MONITORING_DEST,
            "MONITORING_KEY": MONITORING_KEY,
            "DOCKER_SOCKET": DOCKER_SOCKET,
        },
        labels={
            "zimfarm": "",
            "zimtask": "yes",
            "task_id": task["id"],
            "tid": short_id(task["id"]),
            "webapi_uri": webapi_uri,
            "schedule_name": task["schedule_name"],
            # disk usage is accounted for on this container
            RESOURCES_DISK_LABEL: str(task["config"]["resources"]["disk"]),
            # display-only human-readable values
            "human.cpu": str(task["config"]["resources"]["cpu"]),
            "human.memory": format_size(task["config"]["resources"]["memory"]),
            "human.disk": format_size(task["config"]["resources"]["disk"]),
            "human.task-cpu": str(ZIMFARM_TASK_CPUS),
            "human.task-cpuset": str(ZIMFARM_TASK_CPUSET),
        },
        mem_swappiness=0,
        mounts=mounts,
        name=container_name,
        remove=False,  # zimtask containers are pruned periodically
        sysctls=get_sysctl(),
        network_mode=(
            f"container:{get_running_container_name()}"
            if ENVIRONMENT == "development"
            else "bridge"
        ),
    )


def stop_task_worker(client: DockerClient, *, task_id: str, timeout: int = 20):
    container_name = get_container_name(CONTAINER_TASK_IDENT, task_id)
    try:
        stop_container(client, container_name, timeout=timeout)
    except NotFound:
        return False
    else:
        return True


def start_uploader(
    client: DockerClient,
    *,
    task: dict[str, Any],
    kind: str,
    username: str,
    host_workdir: Path,
    upload_dir: Path | str,
    filename: str,
    move: bool,
    delete: bool,
    compress: bool,
    resume: bool,
    watch: bool | None = None,
):
    container_name = upload_container_name(task["id"], filename, kind, unique=False)

    # remove container should it exists (should not)
    try:
        remove_container(client, container=container_name)
        prune_containers(client, {"label": [f"filename={filename}"]})
    except NotFound:
        pass

    docker_image = get_or_pull_image(client, UPLOADER_IMAGE)

    # in container paths
    workdir = Path("/data")
    filepath = workdir.joinpath(filename)

    host_mounts = query_host_mounts(client)
    host_private_key = str(host_mounts[PRIVATE_KEY])
    mounts = [
        Mount(str(workdir), str(host_workdir), type="bind", read_only=not delete),
        Mount(str(PRIVATE_KEY), host_private_key, type="bind", read_only=True),
    ]

    # append the upload_dir and filename to upload_uri
    upload_uri = urllib.parse.urlparse(  # pyright: ignore[reportUnknownVariableType]
        task["upload"][kind]["upload_uri"]
    )
    parts: list[str] = list(upload_uri)  # pyright: ignore[reportUnknownArgumentType]
    # make sure we have a valid upload path
    parts[2] += "/" if not parts[2].endswith("/") else ""
    # ensure upload_dir is not absolute
    parts[2] += os.path.join(re.sub(r"^/", "", str(upload_dir), count=1), filepath.name)
    upload_uri = urllib.parse.urlunparse(parts)

    command = [
        "uploader",
        "--file",
        str(filepath),
        "--upload-uri",
        upload_uri,
        "--username",
        username,
    ]
    if compress:
        command.append("--compress")
    if resume:
        command.append("--resume")
    if move:
        command.append("--move")
    if delete:
        command.append("--delete")
    if watch:
        command += ["--watch", str(watch)]
    if task["upload"][kind]["expiration"]:
        command += ["--delete-after", str(task["upload"][kind]["expiration"])]

    kwargs = {
        "image": docker_image,
        "command": command,
        "detach": True,
        "environment": {"RSA_KEY": str(PRIVATE_KEY)},
        "labels": {
            "zimfarm": "",
            "task_id": task["id"],
            "tid": short_id(task["id"]),
            "schedule_name": task["schedule_name"],
            "filename": filename,
        },
        "mem_swappiness": 0,
        "mounts": mounts,
        "name": container_name,
        "remove": False,
        "network_mode": (
            f"container:{get_running_container_name()}"
            if ENVIRONMENT == "development"
            else "bridge"
        ),
    }
    return run_container(client, **kwargs)


def get_container_logs(
    client: DockerClient, container_name: str, tail: int | Literal["all"] = "all"
):
    try:
        return container_logs(
            client, container=container_name, stdout=True, stderr=True, tail=tail
        ).decode("UTF-8")
    except NotFound:
        return f"Container `{container_name}` gone. Can't get logs"
    except Exception as exc:
        return f"Unable to get logs for `{container_name}`: {exc}"
