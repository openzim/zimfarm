from http import HTTPStatus

import trafaret as t
from flask import request, jsonify, Response, make_response

from common.mongo import Schedules
from utils.offliners import command_information_for
from errors.http import InvalidRequestJSON, ScheduleNotFound
from routes.errors import BadRequest
from routes.schedules.base import ScheduleQueryMixin
from .. import authenticate
from ..base import BaseRoute
from .validators import (
    get_flags_validator,
    language_validator,
    category_validator,
    schedule_validator,
    warehouse_path_validator,
    offliner_validator,
    image_validator,
    resources_validator,
    name_validator,
)


class SchedulesRoute(BaseRoute):
    rule = "/"
    name = "schedules"
    methods = ["GET", "POST"]

    def get(self, *args, **kwargs):
        """Return a list of schedules"""

        # unpack url parameters
        skip = request.args.get("skip", default=0, type=int)
        limit = request.args.get("limit", default=20, type=int)
        skip = 0 if skip < 0 else skip
        limit = 20 if limit <= 0 else limit
        categories = request.args.getlist("category")
        tags = request.args.getlist("tag")
        lang = request.args.getlist("lang")
        name = request.args.get("name")

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
    def post(self, *args, **kwargs):
        """create a new schedule"""

        try:
            document = schedule_validator.check(request.get_json())
        except t.DataError as e:
            raise InvalidRequestJSON(str(e.error))

        # make sure it's not a duplicate
        if Schedules().find_one({"name": document["name"]}, {"name": 1}):
            raise BadRequest(
                "schedule with name `{}` already exists".format(document["name"])
            )

        schedule_id = Schedules().insert_one(document).inserted_id

        return make_response(jsonify({"_id": str(schedule_id)}), HTTPStatus.CREATED)


class SchedulesBackupRoute(BaseRoute):
    rule = "/backup/"
    name = "schedules_backup"
    methods = ["GET"]

    def get(self, *args, **kwargs):
        """Return all schedules backup"""

        projection = {"most_recent_task": 0}
        cursor = Schedules().find({}, projection)
        schedules = [schedule for schedule in cursor]
        return jsonify(schedules)


class ScheduleRoute(BaseRoute, ScheduleQueryMixin):
    rule = "/<string:schedule_name>"
    name = "schedule"
    methods = ["GET", "PATCH", "DELETE"]

    def get(self, schedule_name: str, *args, **kwargs):
        """Get schedule object."""

        query = {"name": schedule_name}
        schedule = Schedules().find_one(query, {"_id": 0})
        if schedule is None:
            raise ScheduleNotFound()

        schedule["config"].update(command_information_for(schedule["config"]))
        return jsonify(schedule)

    @authenticate
    def patch(self, schedule_name: str, *args, **kwargs):
        """Update all properties of a schedule but _id and most_recent_task"""

        query = {"name": schedule_name}
        schedule = Schedules().find_one(query, {"config.task_name": 1})
        if not schedule:
            raise ScheduleNotFound()

        validator = t.Dict(
            t.Key("name", optional=True, trafaret=name_validator),
            t.Key("language", optional=True, trafaret=language_validator),
            t.Key("category", optional=True, trafaret=category_validator),
            t.Key("tags", optional=True, trafaret=t.List(t.String(allow_blank=False))),
            t.Key("enabled", optional=True, trafaret=t.Bool()),
            t.Key("task_name", optional=True, trafaret=offliner_validator),
            t.Key("warehouse_path", optional=True, trafaret=warehouse_path_validator),
            t.Key("image", optional=True, trafaret=image_validator),
            t.Key("resources", optional=True, trafaret=resources_validator),
            t.Key("flags", optional=True, trafaret=t.Dict(allow_extra=["*"])),
        )

        try:
            update = validator.check(request.get_json())
            # empty dict passes the validator but troubles mongo
            if not request.get_json():
                raise t.DataError("Update can't be empty")

            # ensure we test flags according to new task_name if present
            if "task_name" in update:
                if "flags" not in update:
                    raise t.DataError("Can't update offliner without updating flags")
                flags_validator = get_flags_validator(update["task_name"])
            else:
                flags_validator = get_flags_validator(schedule["config"]["task_name"])

            if "flags" in update:
                flags_validator.check(update["flags"])

        except t.DataError as e:
            raise InvalidRequestJSON(str(e.error))

        if "name" in update:
            if Schedules().count_documents({"name": update["name"]}):
                raise BadRequest(
                    "Schedule with name `{}` already exists".format(update["name"])
                )

        config_keys = ["task_name", "warehouse_path", "image", "resources", "flags"]
        mongo_update = {
            f"config.{key}" if key in config_keys else key: value
            for key, value in update.items()
        }

        matched_count = (
            Schedules().update_one(query, {"$set": mongo_update}).matched_count
        )

        if matched_count:
            return Response(status=HTTPStatus.NO_CONTENT)
        else:
            raise ScheduleNotFound()

    @authenticate
    def delete(self, schedule_name: str, *args, **kwargs):
        """Delete a schedule."""

        query = {"name": schedule_name}
        result = Schedules().delete_one(query)

        if result.deleted_count == 0:
            raise ScheduleNotFound()
        else:
            return Response(status=HTTPStatus.NO_CONTENT)
