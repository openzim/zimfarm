#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import humanfriendly


def short_id(task_id):
    """stripped version of task_id for containers/display"""
    return task_id[:5]


def as_pos_int(value):
    if not isinstance(value, int):
        return 0
    return 0 if value < 0 else value


def format_size(value):
    return humanfriendly.format_size(value, binary=True)


def format_key(fingerprint):
    """UUID-hex looking from RSA fingerprint"""
    return (
        f"{fingerprint[0:8]}-{fingerprint[8:12]}-{fingerprint[12:16]}"
        f"-{fingerprint[16:20]}-{fingerprint[20:]}"
    ).upper()
