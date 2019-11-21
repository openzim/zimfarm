#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import pymongo
import trafaret as t
from flask import request, jsonify

from common.mongo import Workers


def list_workers():
    """ list of workers """

    request_args = request.args.to_dict()
    request_args["status"] = request.args.getlist("status")
    validator = t.Dict(
        {
            t.Key("skip", default=0): t.ToInt(gte=0),
            t.Key("limit", default=100): t.ToInt(gt=0, lte=200),
            t.Key("status", optional=True): t.List(t.Enum("online", "offline")),
        }
    )
    request_args = validator.check(request_args)

    # unpack query parameter
    skip, limit = request_args["skip"], request_args["limit"]
    statuses = request_args.get("status")

    query = {}
    if statuses:
        query["status"] = {"$in": statuses}

    count = Workers().count_documents(query)
    projection = {"_id": 1, "status": 1, "hostname": 1}
    cursor = (
        Workers()
        .find(query, projection)
        .sort("status", pymongo.DESCENDING)
        .skip(skip)
        .limit(limit)
    )
    workers = [worker for worker in cursor]

    return jsonify(
        {"meta": {"skip": skip, "limit": limit, "count": count}, "items": workers}
    )
