import base64
import logging
from http import HTTPStatus

import requests
import sqlalchemy as sa
import sqlalchemy.orm as so
from flask import Response, jsonify, make_response, request
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError

import db.models as dbm
from common.schemas.models import ScheduleConfigSchema, ScheduleSchema
from common.schemas.orms import ScheduleFullSchema, ScheduleLightSchema
from common.schemas.parameters import CloneSchema, SchedulesSchema, UpdateSchema
from db import count_from_stmt, dbsession
from errors.http import InvalidRequestJSON, ResourceNotFound, ScheduleNotFound
from routes import auth_info_if_supplied, authenticate, require_perm
from routes.base import BaseRoute
from routes.errors import BadRequest
from routes.utils import raise_if, raise_if_none, remove_secrets_from_response
from utils.offliners import expanded_config
from utils.scheduling import get_default_duration
from utils.token import AccessToken

logger = logging.getLogger(__name__)


class SchedulesRoute(BaseRoute):
    rule = "/"
    name = "schedules"
    methods = ["GET", "POST"]

    @dbsession
    def get(self, session: so.Session):
        """Return a list of schedules"""

        request_args = request.args.to_dict()
        for key in ("category", "tag", "lang"):
            request_args[key] = request.args.getlist(key)
        request_args = SchedulesSchema().load(request_args)

        skip, limit, categories, tags, lang, name = (
            request_args.get("skip"),
            request_args.get("limit"),
            request_args.get("category"),
            request_args.get("tag"),
            request_args.get("lang"),
            request_args.get("name"),
        )

        stmt = (
            sa.select(
                dbm.Schedule.name,
                dbm.Schedule.category,
                so.Bundle(
                    "language",
                    dbm.Schedule.language_code.label("code"),
                    dbm.Schedule.language_name_en.label("name_en"),
                    dbm.Schedule.language_name_native.label("name_native"),
                ),
                so.Bundle(
                    "config",
                    dbm.Schedule.config["task_name"].label("task_name"),
                ),
                so.Bundle(
                    "most_recent_task",
                    dbm.Task.id,
                    dbm.Task.status,
                    dbm.Task.updated_at,
                ),
            )
            .join(dbm.Task, dbm.Schedule.most_recent_task, isouter=True)
            .order_by(dbm.Schedule.name)
        )

        # assemble filters
        if categories:
            stmt = stmt.filter(dbm.Schedule.category.in_(categories))
        if lang:
            stmt = stmt.filter(dbm.Schedule.language_code.in_(lang))
        if tags:
            stmt = stmt.filter(dbm.Schedule.tags.contains(tags))
        if name:
            # "i" flag means case-insensitive search
            stmt = stmt.filter(dbm.Schedule.name.regexp_match(f".*{name}.*", "i"))

        # get total count of items matching the filters
        count = count_from_stmt(session, stmt)

        # get schedules from database
        return jsonify(
            {
                "meta": {"skip": skip, "limit": limit, "count": count},
                "items": list(
                    map(
                        ScheduleLightSchema().dump,
                        session.execute(stmt.offset(skip).limit(limit)).all(),
                    )
                ),
            }
        )

    @authenticate
    @dbsession
    @require_perm("schedules", "create")
    def post(self, session: so.Session, token: AccessToken.Payload):
        """create a new schedule"""

        try:
            document = ScheduleSchema().load(request.get_json())
        except ValidationError as e:
            raise InvalidRequestJSON(e.messages)

        schedule = dbm.Schedule(
            mongo_val=None,
            mongo_id=None,
            name=document["name"],
            category=document["category"],
            periodicity=document["periodicity"],
            tags=document["tags"],
            enabled=document["enabled"],
            config=document["config"],
            notification=document["notification"],
            language_code=document["language"]["code"],
            language_name_en=document["language"]["name_en"],
            language_name_native=document["language"]["name_native"],
        )
        session.add(schedule)

        default_duration = get_default_duration()
        duration = dbm.ScheduleDuration(
            mongo_val=None,
            default=True,
            value=default_duration["value"],
            on=default_duration["on"],
        )
        schedule.durations.append(duration)

        try:
            session.flush()
        except IntegrityError:
            raise BadRequest("Schedule name already exists")

        return make_response(jsonify({"_id": str(schedule.id)}), HTTPStatus.CREATED)


class SchedulesBackupRoute(BaseRoute):
    rule = "/backup/"
    name = "schedules_backup"
    methods = ["GET"]

    @dbsession
    def get(self, session: so.Session):
        """Return all schedules backup"""
        stmt = sa.select(dbm.Schedule).order_by(dbm.Schedule.name)
        return jsonify(
            list(
                map(
                    ScheduleFullSchema().dump,
                    session.execute(stmt).scalars(),
                )
            )
        )


class ScheduleRoute(BaseRoute):
    rule = "/<string:schedule_name>"
    name = "schedule"
    methods = ["GET", "PATCH", "DELETE"]

    @auth_info_if_supplied
    @dbsession
    def get(self, schedule_name: str, token: AccessToken.Payload, session: so.Session):
        """Get schedule object."""

        schedule = dbm.Schedule.get_or_none(session, schedule_name)
        raise_if_none(schedule, ScheduleNotFound)

        schedule.config = expanded_config(schedule.config)

        schedule = ScheduleFullSchema().dump(schedule)

        if not token or not token.get_permission("schedules", "update"):
            remove_secrets_from_response(schedule)

        return jsonify(schedule)

    @authenticate
    @require_perm("schedules", "update")
    @dbsession
    def patch(
        self, schedule_name: str, token: AccessToken.Payload, session: so.Session
    ):
        """Update all properties of a schedule but _id and most_recent_task"""

        schedule = dbm.Schedule.get_or_none(session, schedule_name)
        raise_if_none(schedule, ScheduleNotFound)

        try:
            update = UpdateSchema().load(request.get_json())  # , partial=True
            # empty dict passes the validator but troubles mongo
            raise_if(not request.get_json(), ValidationError, "Update can't be empty")

            # ensure we test flags according to new task_name if present
            if "task_name" in update:
                raise_if(
                    "flags" not in update,
                    ValidationError,
                    "Can't update offliner without updating flags",
                )
                flags_schema = ScheduleConfigSchema.get_offliner_schema(
                    update["task_name"]
                )
            else:
                flags_schema = ScheduleConfigSchema.get_offliner_schema(
                    schedule.config["task_name"]
                )

            if "flags" in update:
                flags_schema().load(update["flags"])
        except ValidationError as e:
            raise InvalidRequestJSON(e.messages)

        config_keys = [
            "task_name",
            "warehouse_path",
            "image",
            "resources",
            "platform",
            "flags",
            "monitor",
        ]

        for key, value in update.items():
            if key in config_keys:
                schedule.config[key] = value
            else:
                setattr(schedule, key, value)

        try:
            session.flush()
        except IntegrityError:
            raise BadRequest("Schedule conflict with another one")

        return Response(status=HTTPStatus.NO_CONTENT)

    @authenticate
    @require_perm("schedules", "delete")
    @dbsession
    def delete(
        self, schedule_name: str, token: AccessToken.Payload, session: so.Session
    ):
        """Delete a schedule."""

        schedule = dbm.Schedule.get_or_none(session, schedule_name)
        raise_if_none(schedule, ScheduleNotFound)
        # First unset most_recent_task to avoid circular dependency issues
        schedule.most_recent_task = None
        session.delete(schedule)

        return Response(status=HTTPStatus.NO_CONTENT)


class ScheduleImageNames(BaseRoute):
    rule = "/<string:schedule_name>/image-names"
    name = "schedule-images"
    methods = ["GET"]

    @authenticate
    @require_perm("schedules", "update")
    def get(self, schedule_name: str, token: AccessToken.Payload):
        """proxy list of tags from docker hub"""
        request_args = request.args.to_dict()
        hub_name = request_args.get("hub_name")

        def make_resp(items):
            return jsonify(
                {
                    "meta": {"skip": 0, "limit": None, "count": len(items)},
                    "items": items,
                }
            )

        try:
            token = base64.b64encode(f"v1:{hub_name}:0".encode("UTF-8")).decode()
            resp = requests.get(
                f"https://ghcr.io/v2/{hub_name}/tags/list",
                headers={
                    "Authorization": f"Bearer {token}",
                    "User-Agent": "Docker-Client/20.10.2 (linux)",
                },
            )
        except Exception as exc:
            logger.error(f"Unable to connect to GHCR Tags list: {exc}")
            return make_resp([])

        raise_if(resp.status_code == HTTPStatus.NOT_FOUND, ResourceNotFound)

        if resp.status_code != HTTPStatus.OK:
            logger.error(f"GHCR responded HTTP {resp.status_code} for {hub_name}")
            return make_resp([])

        try:
            items = [tag for tag in resp.json()["tags"]]
        except Exception as exc:
            logger.error(f"Unexpected GHCR response for {hub_name}: {exc}")
            items = []

        return make_resp(items)


class ScheduleCloneRoute(BaseRoute):
    rule = "/<string:schedule_name>/clone"
    name = "schedule-clone"
    methods = ["POST"]

    @authenticate
    @require_perm("schedules", "create")
    @dbsession
    def post(self, schedule_name: str, token: AccessToken.Payload, session: so.Session):
        """Update all properties of a schedule but _id and most_recent_task"""

        request_json = CloneSchema().load(request.get_json())

        schedule = dbm.Schedule.get_or_none(session, schedule_name)
        raise_if_none(schedule, ScheduleNotFound)

        clone = dbm.Schedule(
            mongo_id=None,
            mongo_val=None,
            name=request_json["name"],
            category=schedule.category,
            periodicity=schedule.periodicity,
            tags=schedule.tags,
            enabled=schedule.tags,
            config=schedule.config,
            notification=schedule.notification,
            language_code=schedule.language_code,
            language_name_en=schedule.language_name_en,
            language_name_native=schedule.language_name_native,
        )
        session.add(clone)

        default_duration = get_default_duration()
        duration = dbm.ScheduleDuration(
            mongo_val=None,
            default=True,
            value=default_duration["value"],
            on=default_duration["on"],
        )
        clone.durations.append(duration)

        session.flush()

        return make_response(jsonify({"_id": str(clone.id)}), HTTPStatus.CREATED)
