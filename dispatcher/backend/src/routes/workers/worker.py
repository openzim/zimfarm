#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import logging
from http import HTTPStatus
from typing import Any, Dict

import marshmallow.fields as mf
import sqlalchemy as sa
import sqlalchemy.orm as so
from flask import Response, jsonify, request
from marshmallow import ValidationError
from marshmallow_sqlalchemy import auto_field
from sqlalchemy.dialects.postgresql import insert

import db.models as dbm
from common import getnow
from common.schemas.orms import BaseSchema
from common.schemas.parameters import SkipLimitSchema, WorkerCheckInSchema
from db import count_from_stmt, dbsession
from errors.http import InvalidRequestJSON
from routes import authenticate, url_object_id
from routes.base import BaseRoute
from routes.errors import BadRequest, InternalError
from routes.utils import raise_if_none
from utils.broadcaster import BROADCASTER

logger = logging.getLogger(__name__)
OFFLINE_DELAY = 20 * 60


class WorkersRoute(BaseRoute):
    rule = "/"
    name = "workers-list"
    methods = ["GET"]

    class Mapper(BaseSchema):
        class Meta:
            model = dbm.Worker

        def get_username(worker: dbm.Worker) -> str:
            return worker.user.username

        def get_status(worker: dbm.Worker) -> str:
            not_seen_since = getnow() - worker.last_seen
            return (
                "online"
                if not_seen_since.total_seconds() < OFFLINE_DELAY
                else "offline"
            )

        def get_resources(worker: dbm.Worker) -> Dict[str, Any]:
            return {
                "cpu": worker.cpu,
                "disk": worker.disk,
                "memory": worker.memory,
            }

        last_ip = auto_field()
        last_seen = auto_field()
        name = auto_field()
        offliners = auto_field()
        resources = mf.Function(serialize=get_resources)
        username = mf.Function(serialize=get_username)
        status = mf.Function(serialize=get_status)

    @dbsession
    def get(self, session: so.Session, *args, **kwargs):
        """list of workers with checked-in data"""

        request_args = SkipLimitSchema().load(request.args.to_dict())
        skip, limit = request_args["skip"], request_args["limit"]

        stmt = (
            sa.select(dbm.Worker)
            .options(so.selectinload(dbm.Worker.user))
            .order_by(dbm.Worker.name)
        )

        count = count_from_stmt(session, stmt)

        return jsonify(
            {
                "meta": {"skip": skip, "limit": limit, "count": count},
                "items": list(
                    map(
                        WorkersRoute.Mapper().dump,
                        session.execute(stmt.offset(skip).limit(limit)).scalars(),
                    )
                ),
            }
        )


class WorkerCheckinRoute(BaseRoute):
    rule = "/<string:name>/check-in"
    name = "worker-checkin"
    methods = ["PUT"]

    @authenticate
    @dbsession
    @url_object_id("name")
    def put(self, session: so.Session, name: str, *args, **kwargs):
        # TODO: is it acceptable that any authenticated user can update the checkin
        # status of any worker ? shouldn't we check authenticated user scope + match
        # between authenticated user id and worker user id
        # see https://github.com/openzim/zimfarm/issues/764
        try:
            request_json = WorkerCheckInSchema().load(request.get_json())
        except ValidationError as e:
            raise InvalidRequestJSON(e.messages)

        user_id = dbm.User.get_id_or_none(session, request_json["username"])
        raise_if_none(user_id, BadRequest, "username not found")

        # let's do an upsert ; conflict on name
        # on conflict, update the selfish, cpu, memory, disk, ...
        upsert_stmt = insert(dbm.Worker).values(
            mongo_val=None,
            mongo_id=None,
            name=name,
            selfish=request_json["selfish"],
            cpu=request_json["cpu"],
            memory=request_json["memory"],
            disk=request_json["disk"],
            offliners=request_json["offliners"],
            platforms=request_json.get("platforms", {}),
            last_seen=getnow(),
            last_ip=None,
            user_id=user_id,
        )
        upsert_stmt = upsert_stmt.on_conflict_do_update(
            index_elements=[
                dbm.Worker.name,
            ],
            set_={
                dbm.Worker.selfish: upsert_stmt.excluded.selfish,
                dbm.Worker.cpu: upsert_stmt.excluded.cpu,
                dbm.Worker.memory: upsert_stmt.excluded.memory,
                dbm.Worker.disk: upsert_stmt.excluded.disk,
                dbm.Worker.offliners: upsert_stmt.excluded.offliners,
                dbm.Worker.platforms: upsert_stmt.excluded.platforms,
                dbm.Worker.last_seen: upsert_stmt.excluded.last_seen,
            },
        )

        session.execute(upsert_stmt)

        worker: dbm.Worker = dbm.Worker.get_or_none(session, name)
        raise_if_none(
            worker,
            InternalError,
            "something bad happened, the worker has been set but can't be found",
        )

        document = {
            "name": worker.name,
            "username": worker.user.username,
            "selfish": worker.selfish,
            "resources": {
                "cpu": worker.cpu,
                "memory": worker.memory,
                "disk": worker.disk,
            },
            "offliners": worker.offliners,
            "platforms": worker.platforms,
            "last_seen": worker.last_seen,
        }

        BROADCASTER.broadcast_worker_checkin(document)

        return Response(status=HTTPStatus.NO_CONTENT)
