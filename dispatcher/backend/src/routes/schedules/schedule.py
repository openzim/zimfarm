from http import HTTPStatus

from flask import request, jsonify, Response, make_response
from marshmallow import ValidationError

from common.mongo import Schedules
from utils.token import AccessToken
from utils.offliners import command_information_for
from errors.http import InvalidRequestJSON, ScheduleNotFound
from routes.errors import BadRequest
from routes.schedules.base import ScheduleQueryMixin
from routes import authenticate, require_perm
from routes.base import BaseRoute
from common.schemas.models import ScheduleConfigSchema, ScheduleSchema
from common.schemas.parameters import SchedulesSchema, UpdateSchema, CloneSchema
from utils.scheduling import get_default_duration


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

        document["duration"] = get_default_duration()
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

    def get(self, schedule_name: str):
        """Get schedule object."""

        query = {"name": schedule_name}
        schedule = Schedules().find_one(query, {"_id": 0})
        if schedule is None:
            raise ScheduleNotFound()

        schedule["config"].update(command_information_for(schedule["config"]))
        return jsonify(schedule)

    @authenticate
    @require_perm("schedules", "update")
    def patch(self, schedule_name: str, token: AccessToken.Payload):
        """Update all properties of a schedule but _id and most_recent_task"""

        query = {"name": schedule_name}
        schedule = Schedules().find_one(query, {"config.task_name": 1})
        if not schedule:
            raise ScheduleNotFound()

        try:
            update = UpdateSchema().load(request.get_json())  # , partial=True
            # empty dict passes the validator but troubles mongo
            if not request.get_json():
                raise ValidationError("Update can't be empty")

            # ensure we test flags according to new task_name if present
            if "task_name" in update:
                if "flags" not in update:
                    raise ValidationError(
                        "Can't update offliner without updating flags"
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

        raise ScheduleNotFound()

    @authenticate
    @require_perm("schedules", "delete")
    def delete(self, schedule_name: str, token: AccessToken.Payload):
        """Delete a schedule."""

        query = {"name": schedule_name}
        result = Schedules().delete_one(query)

        if result.deleted_count == 0:
            raise ScheduleNotFound()
        return Response(status=HTTPStatus.NO_CONTENT)


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
        if Schedules().find_one({"name": new_schedule_name}, {"name": 1}):
            raise BadRequest(
                "schedule with name `{}` already exists".format(new_schedule_name)
            )

        schedule.pop("_id", None)
        schedule.pop("most_recent_task", None)
        schedule.pop("duration", None)
        schedule["name"] = new_schedule_name
        schedule["enabled"] = False
        schedule["duration"] = get_default_duration()

        # insert document
        schedule_id = Schedules().insert_one(schedule).inserted_id

        return make_response(jsonify({"_id": str(schedule_id)}), HTTPStatus.CREATED)
