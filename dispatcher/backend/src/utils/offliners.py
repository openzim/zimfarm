#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import collections
import pathlib

from common.enum import Offliner

# from common.constants import DISALLOW_CAPABILITIES
from typing import List

od = collections.namedtuple("OfflinerDef", ["cmd", "std_output", "std_stats"])
OFFLINER_DEFS = {
    Offliner.gutenberg: od("gutenberg2zim", False, False),
    Offliner.sotoki: od("sotoki", True, True),
    Offliner.wikihow: od("wikihow2zim", True, True),
    Offliner.ifixit: od("ifixit2zim", True, True),
    Offliner.mwoffliner: od("mwoffliner", "outputDirectory", False),
    Offliner.youtube: od("youtube2zim-playlists", True, False),
    Offliner.ted: od("ted2zim-multi", True, False),
    Offliner.openedx: od("openedx2zim", True, False),
    Offliner.nautilus: od("nautiluszim", True, False),
    Offliner.zimit: od("zimit", True, "statsFilename"),
    Offliner.kolibri: od("kolibri2zim", True, False),
}


def mount_point_for(offliner):
    """Path to mount task volume in scraper"""
    if offliner == Offliner.phet:
        return pathlib.Path("/phet/dist")
    return pathlib.Path("/output")


def command_for(offliner, flags, mount_point):
    """command:list to be passed to docker run

    for an offliner,  flags:dict and a mount_point:Path (task volume)"""

    if offliner == Offliner.phet:
        return ["/bin/bash", "-c", "'cd /phet && npm i && npm start'"]

    offliner_def = OFFLINER_DEFS[offliner]
    cmd = offliner_def.cmd
    if offliner_def.std_output:
        flags[
            offliner_def.std_output
            if isinstance(offliner_def.std_output, str)
            else "output"
        ] = str(mount_point)
    if offliner_def.std_stats:
        flags[
            offliner_def.std_stats
            if isinstance(offliner_def.std_stats, str)
            else "stats-filename"
        ] = str(mount_point_for(offliner) / "task_progress.json")

    if offliner == Offliner.gutenberg:
        # multiple ZIM expects a directory
        if flags.get("one-language-one-zim"):
            flags["one-language-one-zim"] = str(mount_point)
        if flags.get("one-language-one-zim") is False:
            del flags["one-language-one-zim"]
        # when not using multiple ZIM, scraper uses cwd as output (/output)
    if offliner == Offliner.sotoki:
        flags["mirror"] = flags.get(
            "mirror", "https://s3.us-west-1.wasabisys.com/org-kiwix-stackexchange"
        )
        flags["redis-url"] = "unix:///var/run/redis.sock"
        flags["keep-redis"] = True
    if offliner == Offliner.zimit:
        if "adminEmail" not in flags:
            flags["adminEmail"] = "contact+zimfarm@kiwix.org"
    return [cmd] + compute_flags(flags)


def docker_config_for(offliner):
    # Note: in docker, --shm-size sets the size of /dev/shm
    # it is taken out of --memory (if set)
    extra_config = {}
    if offliner == Offliner.zimit:
        extra_config.update({"shm": 2 ** 30})
    return extra_config


def compute_flags(flags, use_equals=True):
    """flat list of params from dict of flags"""
    params: [str] = []
    for key, value in flags.items():
        if value is True:
            params.append(f"--{key}")
            continue
        if value is False:
            continue
        elif isinstance(value, list):
            for item in value:
                if use_equals:
                    params.append(f'--{key}="{item}"')
                else:
                    params.append(f"--{key}")
                    params.append(f"{item}")
        else:
            if use_equals:
                params.append(f'--{key}="{value}"')
            else:
                params.append(f"--{key}")
                params.append(f"{value}")
    return params


def expanded_config(config):
    # update image name with registry if required
    config["image"]["name"] = Offliner.get_image_name(config["task_name"])

    # mount-point is offliner-specific
    config["mount_point"] = str(mount_point_for(config["task_name"]))
    # computed command flags
    config["command"] = command_for(
        config["task_name"], config["flags"], config["mount_point"]
    )
    # workers uses string version
    config["str_command"] = build_str_command(config["command"])
    # offliners can specify additional docker options (capabilities)
    docker_options = docker_config_for(config["task_name"])

    def get_shm(offliner_shm=None, config_shm=None):
        # use largest of /dev/shm specified (in config vs in offliner rule)
        if offliner_shm and config_shm:
            dev_shm = max([offliner_shm, config_shm])
        else:
            dev_shm = config_shm or offliner_shm

        # use at most memory for /dev/shm if specified and above memory
        if dev_shm and dev_shm > config["resources"]["memory"]:
            dev_shm = config["resources"]["memory"]
        return dev_shm

    dev_shm = get_shm(
        offliner_shm=docker_options.pop("shm", None),
        config_shm=config["resources"].get("shm"),
    )
    if dev_shm:
        config["resources"]["shm"] = dev_shm

    # offliners can update resources
    config["resources"].update(docker_options)

    return config


def build_str_command(args: List[str]):
    """string version of the command to be run by the worker"""
    return " ".join(args)
