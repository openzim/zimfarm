from http import HTTPStatus

from flask import request, jsonify, Response, make_response
from marshmallow import Schema, fields, validate
from marshmallow.exceptions import ValidationError

from common.mongo import Schedules
from common.enum import ScheduleCategory
from utils.offliners import command_information_for
from errors.http import InvalidRequestJSON, ScheduleNotFound
from routes.errors import BadRequest
from routes.schedules.base import ScheduleQueryMixin
from routes import authenticate
from routes.base import BaseRoute
from common.schemas import (
    LanguageSchema,
    ResourcesSchema,
    validate_category,
    validate_warehouse_path,
    validate_offliner,
    DockerImageSchema,
    ScheduleConfigSchema,
    ScheduleSchema,
)


class SchedulesRoute(BaseRoute):
    rule = "/"
    name = "schedules"
    methods = ["GET", "POST"]

    def get(self, *args, **kwargs):
        """Return a list of schedules"""

        # unpack url parameters
        class RequestArgsSchema(Schema):
            skip = fields.Integer(
                required=False, missing=0, validate=validate.Range(min=0)
            )
            limit = fields.Integer(
                required=False, missing=20, validate=validate.Range(min=0, max=200)
            )
            category = fields.List(
                fields.String(validate=validate.OneOf(ScheduleCategory.all())),
                required=False,
            )
            tag = fields.List(fields.String(), required=False)
            lang = fields.List(fields.String(), required=False)
            name = fields.String(required=False, validate=validate.Length(min=2))

        request_args = request.args.to_dict()
        for key in ("category", "tag", "lang"):
            request_args[key] = request.args.getlist(key)
        request_args = RequestArgsSchema().load(request_args)

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
    def post(self, *args, **kwargs):
        """create a new schedule"""

        try:
            document = ScheduleSchema().load(request.get_json())
        except ValidationError as e:
            raise InvalidRequestJSON(str(e.messages))

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

        class UpdateSchema(Schema):
            name = fields.String(required=False, validate=validate.Length(min=2))
            language = fields.Nested(LanguageSchema(), required=False)
            category = fields.String(required=False, validate=validate_category)
            tags = fields.List(fields.String(), required=False)
            enabled = fields.Boolean(required=False, truthy={True}, falsy={False})
            task_name = fields.String(required=False, validate=validate_offliner)
            warehouse_path = fields.String(
                required=False, validate=validate_warehouse_path
            )
            image = fields.Nested(DockerImageSchema, required=False)
            resources = fields.Nested(ResourcesSchema, required=False)
            flags = fields.Dict(required=False)

        try:
            update = UpdateSchema().load(request.json)  # , partial=True
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
            raise InvalidRequestJSON(str(e.messages))

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
