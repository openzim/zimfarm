#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from flask import jsonify

from common.mongo import Workers


def list():
    """ list of workers """

    # get aggregation project stage
    project = {
        "hostname": 1,
        "status": 1,
        "session": 1,
        "heartbeat": {"$arrayElemAt": ["$heartbeats", -1]},
        "load_average": {},
    }
    tags = ["1_min", "5_mins", "15_mins"]
    for tag in tags:
        project["load_average"][tag] = {
            "$arrayElemAt": ["$load_averages.{}".format(tag), -1]
        }
    pipeline = [
        {"$project": project},
        {"$sort": {"status": -1}},  # online comes before offline
    ]

    # get list of workers
    workers = [worker for worker in Workers().aggregate(pipeline)]
    return jsonify(workers)
