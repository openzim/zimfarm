#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import logging
from http import HTTPStatus

import pymongo
from flask import request, jsonify, Response
from marshmallow import ValidationError

from errors.http import InvalidRequestJSON
from routes import authenticate, url_object_id
from common import getnow
from common.mongo import Workers
from routes.base import BaseRoute
from utils.broadcaster import BROADCASTER
from common.schemas.parameters import SkipLimitSchema, WorkerCheckInSchema

logger = logging.getLogger(__name__)
OFFLINE_DELAY = 20 * 60


class WorkersRoute(BaseRoute):
    rule = "/"
    name = "workers-list"
    methods = ["GET"]

    def get(self, *args, **kwargs):
        """ list of workers with checked-in data """

        def add_status(worker):
            not_seen_since = getnow() - worker["last_seen"]
            worker["status"] = (
                "online"
                if not_seen_since.total_seconds() < OFFLINE_DELAY
                else "offline"
            )
            return worker

        request_args = SkipLimitSchema().load(request.args.to_dict())
        skip, limit = request_args["skip"], request_args["limit"]

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
        try:
            request_json = WorkerCheckInSchema().load(request.get_json())
        except ValidationError as e:
            raise InvalidRequestJSON(e.messages)

        document = {
            "name": name,
            "username": request_json["username"],
            "resources": {
                "cpu": request_json["cpu"],
                "memory": request_json["memory"],
                "disk": request_json["disk"],
            },
            "offliners": request_json["offliners"],
            "last_seen": getnow(),
        }
        Workers().replace_one({"name": name}, document, upsert=True)

        BROADCASTER.broadcast_worker_checkin(document)

        return Response(status=HTTPStatus.NO_CONTENT)
