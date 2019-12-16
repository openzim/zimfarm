#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import logging
import datetime
from http import HTTPStatus

import pymongo
from flask import request, jsonify, Response
from marshmallow import Schema, fields, validate
from marshmallow.exceptions import ValidationError

from errors.http import InvalidRequestJSON
from routes import authenticate, url_object_id
from common.mongo import Workers
from common.enum import Offliner
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

        class SkipLimitSchema(Schema):
            skip = fields.Integer(
                required=False, missing=0, validate=validate.Range(min=0)
            )
            limit = fields.Integer(
                required=False, missing=20, validate=validate.Range(min=0, max=200)
            )

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
        class JsonRequestSchema(Schema):
            username = fields.String(required=True)
            cpu = fields.Integer(required=True, validate=validate.Range(min=0))
            memory = fields.Integer(required=True, validate=validate.Range(min=0))
            disk = fields.Integer(required=True, validate=validate.Range(min=0))
            offliners = fields.List(
                fields.String(validate=validate.OneOf(Offliner.all())), required=True
            )

        try:
            request_json = JsonRequestSchema().load(request.get_json())
        except ValidationError as e:
            raise InvalidRequestJSON(str(e.messages))

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
