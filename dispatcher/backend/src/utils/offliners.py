#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import copy
import pathlib

from common.enum import Offliner


def mount_point_for(offliner):
    """ Path to mount task volume in scraper """
    if offliner == Offliner.phet:
        return pathlib.Path("/phet/dist")
    if offliner == Offliner.sotoki:
        return pathlib.Path("/work")
    return pathlib.Path("/output")


def command_for(offliner, flags, mount_point):
    """ command:list to be passed to docker run

        for an offliner,  flags:dict and a mount_point:Path (task volume) """
    if offliner == Offliner.phet:
        return ["/bin/bash", "-c", "cd /phet && npm i && npm start"]
    if offliner == Offliner.gutenberg:
        return [
            "gutenberg2zim",
            "--complete",
            "--formats",
            "all",
            "--one-language-one-zim",
            str(mount_point),
        ]
    if offliner == Offliner.sotoki:
        command_flags = copy.deepcopy(flags)
        domain = command_flags.pop("domain")
        publisher = command_flags.pop("publisher", "Kiwix")
        return ["sotoki", domain, publisher] + compute_flags(command_flags)
    if offliner == Offliner.mwoffliner:
        cmd = "mwoffliner"
        flags["outputDirectory"] = str(mount_point)
    if offliner == Offliner.youtube:
        cmd = "youtube2zim"
        flags["output"] = str(mount_point)
    return [cmd] + compute_flags(flags)


def compute_flags(flags, use_equals=True):
    """ flat list of params from dict of flags """
    params: [str] = []
    for key, value in flags.items():
        if value is True:
            params.append(f"--{key}")
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


def command_information_for(config):
    info = {}
    info["mount_point"] = str(mount_point_for(config["task_name"]))
    info["command"] = command_for(
        config["task_name"], config["flags"], info["mount_point"]
    )
    info["str_command"] = " ".join(info["command"])
    return info
