#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import os
import multiprocessing

import psutil
import humanfriendly

from common.constants import DEFAULT_CPU_SHARE, CONTAINER_SCRAPER_PREFIX

def query_containers_resources(docker_api):
    cpu_shares = 0
    memory = 0
    for container in docker_api.containers(filters={"name": CONTAINER_SCRAPER_PREFIX}):
        inspect_data = docker_api.inspect_container(container["Id"])
        cpu_shares += inspect_data["HostConfig"]["CpuShares"] or DEFAULT_CPU_SHARE
        memory += inspect_data["HostConfig"]["Memory"]

    return {"cpu_shares": cpu_shares, "memory": memory}


def query_host_stats(docker_api, workdir):

    # disk space
    workir_fs_stats = os.statvfs(workdir)
    disk_avail = workir_fs_stats.f_bavail * workir_fs_stats.f_frsize

    # query cpu and ram usage in our containers
    stats = query_containers_resources(docker_api)

    # CPU cores
    cpu_present = multiprocessing.cpu_count()
    cpu_total = min([int(os.getenv("MAX_CPUS", cpu_present)), cpu_present])
    cpu_used = stats["cpu_shares"] // DEFAULT_CPU_SHARE
    cpu_avail = cpu_total - cpu_used

    # RAM
    mem_present = psutil.virtual_memory().total
    mem_total = min(
        [
            humanfriendly.parse_size(
                os.getenv("MAX_RAM", humanfriendly.format_size(mem_present))
            ),
            mem_present,
        ]
    )
    mem_used = stats["memory"]
    mem_avail = mem_total - mem_used

    return {
        "cpu": {"total": cpu_total, "available": cpu_avail},
        "disk": {"available": disk_avail},
        "memory": {"total": mem_total, "available": mem_avail},
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


def create_volume(client, task_id):
    pass


def start_container(client, image, kwargs, volumes, environ, mem_limit):

    # mem_limit=
    pass
