import base64
import logging
from http import HTTPStatus

import requests
from flask import Response, jsonify, make_response, request
from marshmallow import ValidationError

from common.mongo import RequestedTasks, Schedules, Tasks
from common.schemas.models import ScheduleConfigSchema, ScheduleSchema
from common.schemas.parameters import CloneSchema, SchedulesSchema, UpdateSchema
from errors.http import InvalidRequestJSON, ResourceNotFound, ScheduleNotFound
from routes import auth_info_if_supplied, authenticate, require_perm
from routes.base import BaseRoute
from routes.errors import BadRequest
from routes.schedules.base import ScheduleQueryMixin
from routes.utils import raise_if, raise_if_none, remove_secrets_from_response
from utils.offliners import expanded_config
from utils.scheduling import get_default_duration
from utils.token import AccessToken

logger = logging.getLogger(__name__)


class SchedulesRoute(BaseRoute):
    rule = "/"
    name = "schedules"
    methods = ["GET", "POST"]

    def get(self):
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

        # assemble filters
        query = {}
        if categories:
            query["category"] = {"$in": categories}
        if lang:
            query["language.code"] = {"$in": lang}
        if tags:
            query["tags"] = {"$all": tags}
        if name:
            query["name"] = {"$regex": r".*{}.*".format(name), "$options": "i"}

        # get schedules from database
        projection = {
            "_id": 0,
            "name": 1,
            "category": 1,
            "language": 1,
            "config.task_name": 1,
            "most_recent_task": 1,
        }
        cursor = Schedules().find(query, projection).skip(skip).limit(limit)
        count = Schedules().count_documents(query)
        schedules = [schedule for schedule in cursor]

        return jsonify(
            {"meta": {"skip": skip, "limit": limit, "count": count}, "items": schedules}
        )

    @authenticate
    @require_perm("schedules", "create")
    def post(self, token: AccessToken.Payload):
        """create a new schedule"""

        try:
            document = ScheduleSchema().load(request.get_json())
        except ValidationError as e:
            raise InvalidRequestJSON(e.messages)

        # make sure it's not a duplicate
        if Schedules().find_one({"name": document["name"]}, {"name": 1}):
            raise BadRequest(
                "schedule with name `{}` already exists".format(document["name"])
            )

        document["duration"] = {"default": get_default_duration(), "workers": {}}
        schedule_id = Schedules().insert_one(document).inserted_id

        return make_response(jsonify({"_id": str(schedule_id)}), HTTPStatus.CREATED)


class SchedulesBackupRoute(BaseRoute):
    rule = "/backup/"
    name = "schedules_backup"
    methods = ["GET"]

    def get(self):
        """Return all schedules backup"""

        projection = {"most_recent_task": 0}
        cursor = Schedules().find({}, projection)
        schedules = [schedule for schedule in cursor]
        return jsonify(schedules)


class ScheduleRoute(BaseRoute, ScheduleQueryMixin):
    rule = "/<string:schedule_name>"
    name = "schedule"
    methods = ["GET", "PATCH", "DELETE"]

    @auth_info_if_supplied
    def get(self, schedule_name: str, token: AccessToken.Payload):
        """Get schedule object."""

        query = {"name": schedule_name}
        schedule = Schedules().find_one(query, {"_id": 0})
        raise_if_none(schedule, ScheduleNotFound)

        schedule["config"] = expanded_config(schedule["config"])
        if not token or not token.get_permission("schedules", "update"):
            remove_secrets_from_response(schedule)

        return jsonify(schedule)

    @authenticate
    @require_perm("schedules", "update")
    def patch(self, schedule_name: str, token: AccessToken.Payload):
        """Update all properties of a schedule but _id and most_recent_task"""

        query = {"name": schedule_name}
        schedule = Schedules().find_one(query, {"config.task_name": 1})
        raise_if(not schedule, ScheduleNotFound)
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
                    schedule["config"]["task_name"]
                )

            if "flags" in update:
                flags_schema().load(update["flags"])
        except ValidationError as e:
            raise InvalidRequestJSON(e.messages)

        if "name" in update:
            raise_if(
                Schedules().count_documents({"name": update["name"]}),
                BadRequest,
                "Schedule with name `{}` already exists".format(update["name"]),
            )

        config_keys = [
            "task_name",
            "warehouse_path",
            "image",
            "resources",
            "platform",
            "flags",
            "monitor",
        ]
        mongo_update = {
            f"config.{key}" if key in config_keys else key: value
            for key, value in update.items()
        }

        matched_count = (
            Schedules().update_one(query, {"$set": mongo_update}).matched_count
        )

        if matched_count:
            tasks_query = {"schedule_name": schedule_name}
            if "name" in update:
                Tasks().update_many(
                    tasks_query, {"$set": {"schedule_name": update["name"]}}
                )

                RequestedTasks().update_many(
                    tasks_query, {"$set": {"schedule_name": update["name"]}}
                )

            return Response(status=HTTPStatus.NO_CONTENT)

        raise ScheduleNotFound()

    @authenticate
    @require_perm("schedules", "delete")
    def delete(self, schedule_name: str, token: AccessToken.Payload):
        """Delete a schedule."""

        query = {"name": schedule_name}
        result = Schedules().delete_one(query)

        raise_if(result.deleted_count == 0, ScheduleNotFound)
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


class ScheduleCloneRoute(BaseRoute, ScheduleQueryMixin):
    rule = "/<string:schedule_name>/clone"
    name = "schedule-clone"
    methods = ["POST"]

    @authenticate
    @require_perm("schedules", "create")
    def post(self, schedule_name: str, token: AccessToken.Payload):
        """Update all properties of a schedule but _id and most_recent_task"""

        query = {"name": schedule_name}
        schedule = Schedules().find_one(query)
        if not schedule:
            raise ScheduleNotFound()

        request_json = CloneSchema().load(request.get_json())
        new_schedule_name = request_json["name"]

        # ensure it's not a duplicate
        raise_if(
            Schedules().find_one({"name": new_schedule_name}, {"name": 1}),
            BadRequest,
            "schedule with name `{}` already exists".format(new_schedule_name),
        )

        schedule.pop("_id", None)
        schedule.pop("most_recent_task", None)
        schedule.pop("duration", None)
        schedule["name"] = new_schedule_name
        schedule["enabled"] = False
        schedule["duration"] = {"default": get_default_duration(), "workers": {}}

        # insert document
        schedule_id = Schedules().insert_one(schedule).inserted_id

        return make_response(jsonify({"_id": str(schedule_id)}), HTTPStatus.CREATED)
