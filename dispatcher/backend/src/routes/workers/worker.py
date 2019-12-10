#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import logging
import datetime
from http import HTTPStatus

import pymongo
import trafaret as t
from flask import request, jsonify, Response

from errors.http import InvalidRequestJSON
from routes import authenticate, url_object_id
from common.mongo import Workers
from routes.base import BaseRoute
from utils.broadcaster import BROADCASTER

logger = logging.getLogger(__name__)
OFFLINE_DELAY = 20 * 60


class WorkersRoute(BaseRoute):
    rule = "/"
    name = "workers-list"
    methods = ["GET"]

    def get(self, *args, **kwargs):
        """ list of workers with checked-in data """

        now = datetime.datetime.now()

        def add_status(worker):
            not_seen_since = now - worker["last_seen"]
            worker["status"] = (
                "online"
                if not_seen_since.total_seconds() < OFFLINE_DELAY
                else "offline"
            )
            return worker

        skip = request.args.get("skip", default=0, type=int)
        limit = request.args.get("limit", default=20, type=int)
        skip = 0 if skip < 0 else skip
        limit = 20 if limit <= 0 else limit

        query = {}
        count = Workers().count_documents(query)
        projection = {
            "_id": 0,
            "name": 1,
            "username": 1,
            "offliners": 1,
            "resources": 1,
            "last_seen": 1,
        }
        cursor = (
            Workers()
            .find(query, projection)
            .sort("name", pymongo.ASCENDING)
            .skip(skip)
            .limit(limit)
        )
        workers = list(map(add_status, cursor))

        return jsonify(
            {"meta": {"skip": skip, "limit": limit, "count": count}, "items": workers}
        )


class WorkerCheckinRoute(BaseRoute):
    rule = "/<string:name>/check-in"
    name = "worker-checkin"
    methods = ["PUT"]

    @authenticate
    @url_object_id("name")
    def put(self, name: str, *args, **kwargs):

        validator = t.Dict(
            {
                t.Key("username", optional=False): t.String(),
                t.Key("cpu", optional=False): t.ToInt(gte=0),
                t.Key("memory", optional=False): t.ToInt(gte=0),
                t.Key("disk", optional=False): t.ToInt(gte=0),
                t.Key("offliners", optional=False): t.List(
                    t.Enum("mwoffliner", "youtube", "gutenberg", "ted", "phet")
                ),
            }
        )

        try:
            request_json = validator.check(request.get_json())
        except t.DataError as e:
            raise InvalidRequestJSON(str(e.error))

        document = {
            "name": name,
            "username": request_json["username"],
            "resources": {
                "cpu": request_json["cpu"],
                "memory": request_json["memory"],
                "disk": request_json["disk"],
            },
            "offliners": request_json["offliners"],
            "last_seen": datetime.datetime.now(),
        }
        Workers().replace_one({"name": name}, document, upsert=True)

        BROADCASTER.broadcast_worker_checkin(document)

        return Response(status=HTTPStatus.NO_CONTENT)
