#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import pathlib

from common.constants import (
    OFFLINER_PHET,
    OFFLINER_GUTENBERG,
    OFFLINER_MWOFFLINER,
    OFFLINER_YOUTUBE,
)


def mount_point_for(offliner):
    """ Path to mount task volume in scraper """
    if offliner == OFFLINER_PHET:
        return pathlib.Path("/phet/dist")
    return pathlib.Path("/output")


def command_for(offliner, flags, mount_point):
    """ command:list to be passed to docker run

        for an offliner,  flags:dict and a mount_point:Path (task volume) """
    if offliner == OFFLINER_PHET:
        return ["/bin/bash", "-c", "cd /phet && npm i && npm start"]
    elif offliner == OFFLINER_GUTENBERG:
        return [
            "gutenberg2zim",
            "--complete",
            "--formats",
            "all",
            "--one-language-one-zim",
            str(mount_point),
        ]

    if offliner == OFFLINER_MWOFFLINER:
        cmd = "mwoffliner"
        flags["outputDirectory"] = str(mount_point)
    if offliner == OFFLINER_YOUTUBE:
        cmd = "youtube2zim"
        flags["output"] = str(mount_point)
    return [cmd] + compute_flags(flags)


def compute_flags(flags):
    """ flat list of params from dict of flags """
    params: [str] = []
    for key, value in flags.items():
        if value is True:
            params.append(f"--{key}")
        elif isinstance(value, list):
            for item in value:
                params.append(f'--{key}="{item}"')
        else:
            params.append(f'--{key}="{value}"')
    return params
