#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import os
import pathlib

import docker
from docker.types import Mount

from common import logger
from common.constants import (
    DEFAULT_CPU_SHARE,
    CONTAINER_SCRAPER_PREFIX,
    ZIMFARM_DISK_SPACE,
    ZIMFARM_CPUS,
    ZIMFARM_MEMORY,
    CONTAINER_TASK_PREFIX,
    USE_PUBLIC_DNS,
    CONTAINER_DNSCACHE_PREFIX,
    TASK_WORKER_IMAGE,
    DOCKER_SOCKET,
    PRIVATE_KEY,
)
from common.utils import short_id


def query_containers_resources(docker_api):
    cpu_shares = 0
    memory = 0
    disk = 0
    for container in docker_api.containers(filters={"name": CONTAINER_SCRAPER_PREFIX}):
        inspect_data = docker_api.inspect_container(container["Id"])
        cpu_shares += inspect_data["HostConfig"]["CpuShares"] or DEFAULT_CPU_SHARE
        memory += inspect_data["HostConfig"]["Memory"]
        try:
            disk += int(container["Labels"].get("resources_disk", 0))
        except Exception:
            pass  # improper label

    return {"cpu_shares": cpu_shares, "memory": memory, "disk": disk}


def query_host_stats(docker_api, workdir):

    # query cpu and ram usage in our containers
    stats = query_containers_resources(docker_api)

    # disk space
    workir_fs_stats = os.statvfs(workdir)
    disk_free = workir_fs_stats.f_bavail * workir_fs_stats.f_frsize
    disk_avail = min([ZIMFARM_DISK_SPACE - stats["disk"], disk_free])

    # CPU cores
    cpu_used = stats["cpu_shares"] // DEFAULT_CPU_SHARE
    cpu_avail = ZIMFARM_CPUS - cpu_used

    # RAM
    mem_used = stats["memory"]
    mem_avail = ZIMFARM_MEMORY - mem_used

    return {
        "cpu": {"total": ZIMFARM_CPUS, "available": cpu_avail},
        "disk": {"total": ZIMFARM_DISK_SPACE, "available": disk_avail},
        "memory": {"total": ZIMFARM_MEMORY, "available": mem_avail},
    }


def query_container_stats(workdir):
    workir_fs_stats = os.statvfs(workdir)
    avail_disk = workir_fs_stats.f_bavail * workir_fs_stats.f_frsize

    with open("/sys/fs/cgroup/memory/memory.limit_in_bytes", "r") as fp:
        mem_total = int(fp.read().strip())
    with open("/sys/fs/cgroup/memory/memory.usage_in_bytes", "r") as fp:
        mem_used = int(fp.read().strip())
    mem_avail = mem_total - mem_used

    with open("/sys/fs/cgroup/cpuacct/cpuacct.usage_percpu", "r") as fp:
        cpu_total = len(fp.read().strip().split())

    return {
        "cpu": {"total": cpu_total},
        "disk": {"available": avail_disk},
        "memory": {"total": mem_total, "available": mem_avail},
    }


def query_host_mounts(docker_client, workdir):
    keys = [DOCKER_SOCKET, PRIVATE_KEY, workdir]
    own_name = os.getenv("HOSTNAME", "zimfarm_worker-manager")
    mounts = {}
    for mount in docker_client.api.inspect_container(own_name)["Mounts"]:
        dest = pathlib.Path(mount["Destination"])
        if dest in keys:
            key = keys[keys.index(dest)]
            mounts[key] = pathlib.Path(mount["Source"])
    return mounts


def task_container_name(task_id):
    return f"{CONTAINER_TASK_PREFIX}{short_id(task_id)}"


def dnscache_container_name(task_id):
    return f"{CONTAINER_DNSCACHE_PREFIX}{short_id(task_id)}"


def create_volume(docker_client, task_id):
    pass


def get_ip_address(docker_client, name):
    """ IP Address (first) of a named container """
    return docker_client.api.inspect_container(name)["NetworkSettings"]["IPAddress"]


def start_dnscache(docker_client, name):
    environment = {"USE_PUBLIC_DNS": "yes" if USE_PUBLIC_DNS else "no"}
    image = docker_client.images.pull("openzim/dnscache", tag="latest")
    return docker_client.containers.run(
        image, detach=True, name=name, environment=environment
    )


def stop_container(docker_client, name, timeout):
    container = docker_client.get(name)
    container.stop(timeout=timeout)


def start_scraper(
    docker_client,
    name,
    task,
    image,
    tag,
    command,
    mounts,
    environment,
    mem_limit,
    cpu_shares,
):
    docker_image = docker_client.images.pull(image, tag=tag)
    return docker_client.containers.run(
        image=docker_image,
        command=command,
        auto_remove=False,
        cpu_shares=cpu_shares,
        detach=True,
        environment=environment,
        labels={
            "task_id": task["_id"],
            "tid": short_id(task["_id"]),
            "schedule_id": task["schedule_id"],
            "schedule_name": task["schedule_name"],
            "resources_cpu": task["resouces"]["cpu"],
            "resources_memory": task["resouces"]["memory"],
            "resources_disk": task["resouces"]["disk"],
        },
        mem_limit=mem_limit,
        mem_swappiness=0,
        mounts=[],
        name=name,
        dns=[get_ip_address(docker_client, dnscache_container_name(task["_id"]))],
        remove=False,
    )


def start_task_worker(docker_client, task, webapi_uri, username, workdir, worker_name):
    container_name = task_container_name(task["_id"])

    # remove container should it exists (should not)
    try:
        docker_client.containers.get(container_name).remove()
    except docker.errors.NotFound:
        pass

    image, tag = TASK_WORKER_IMAGE.rsplit(":", 1)
    if tag == "local":
        docker_image = docker_client.images.get(TASK_WORKER_IMAGE)
    else:
        docker_image = docker_client.images.pull(image, tag=tag)

    # mounts will be attached to host's fs, not this one
    host_mounts = query_host_mounts(docker_client, workdir)
    # host_task_workdir = str(
    #     host_mounts.get(workdir, pathlib.Path("/tmp")).joinpath(task["_id"])
    # )
    host_task_workdir = str(host_mounts.get(workdir, pathlib.Path("/tmp")))
    host_docker_socket = str(host_mounts.get(DOCKER_SOCKET))
    host_private_key = str(host_mounts.get(PRIVATE_KEY))
    mounts = [
        Mount(str(workdir), host_task_workdir, type="bind"),
        Mount(str(DOCKER_SOCKET), host_docker_socket, type="bind", read_only=True),
        Mount(str(PRIVATE_KEY), host_private_key, type="bind", read_only=True),
    ]

    logger.debug(f"docker run {container_name}")
    return docker_client.containers.run(
        image=docker_image,
        command=["task-worker", "--task-id", task["_id"]],
        detach=True,
        environment={
            "USERNAME": username,
            "WORKDIR": str(workdir),
            "WEB_API_URI": webapi_uri,
            "WORKER_NAME": worker_name,
        },
        labels={
            "zimtask": "yes",
            "task_id": task["_id"],
            "tid": short_id(task["_id"]),
            "schedule_id": task["schedule_id"],
            "schedule_name": task["schedule_name"],
        },
        mem_swappiness=0,
        mounts=mounts,
        name=container_name,
        remove=False,  # zimtask containers are pruned periodically
    )


def stop_task_worker(docker_client, task_id, timeout: int = 20):
    container_name = task_container_name(task_id)
    try:
        docker_client.containers.get(container_name).stop(timeout=timeout)
    except docker.errors.NotFound:
        return False
    else:
        return True
