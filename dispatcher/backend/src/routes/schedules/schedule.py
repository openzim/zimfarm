import json
from datetime import datetime
from http import HTTPStatus

import trafaret as t
from flask import request, jsonify, Response

from common.mongo import Schedules
from errors.http import InvalidRequestJSON, ScheduleNotFound
from routes.errors import BadRequest
from routes.schedules.base import ScheduleQueryMixin
from .. import authenticate
from ..base import BaseRoute
from .validators import (
    config_validator,
    language_validator,
    category_validator,
    schedule_validator,
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
        queue = request.args.getlist("queue")
        name = request.args.get("name")

        # assemble filters
        query = {}
        if categories:
            query["category"] = {"$in": categories}
        if queue:
            query["config.queue"] = {"$in": queue}
        if lang:
            query["language.code"] = {"$in": lang}
        if tags:
            query["tags"] = {"$all": tags}
        if name:
            query["name"] = {"$regex": r".*{}.*".format(name), "$options": "i"}

        # get schedules from database
        projection = {
            "_id": 1,
            "name": 1,
            "category": 1,
            "language": 1,
            "config.task_name": 1,
            "most_recent_task": 1,
        }
        cursor = Schedules().find(query, projection).skip(skip).limit(limit)
        count = Schedules().count_documents(query)
        schedules = [schedule for schedule in cursor]

        # task this month
        utc_now = datetime.utcnow()
        first_day_this_month = datetime(year=utc_now.year, month=utc_now.month, day=1)
        for schedule in schedules:
            most_recent_task_updated_at = schedule.get("most_recent_task", {}).get(
                "updated_at"
            )
            if (
                most_recent_task_updated_at
                and most_recent_task_updated_at > first_day_this_month
            ):
                schedule["task_this_month"] = schedule["most_recent_task"]
            else:
                schedule["task_this_month"] = None

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

        return Response(json.dumps({"_id": str(schedule_id)}), HTTPStatus.CREATED)


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
    rule = "/<string:schedule>"
    name = "schedule"
    methods = ["GET", "PATCH", "DELETE"]

    def get(self, schedule: str, *args, **kwargs):
        """Get schedule object."""

        query = self.get_schedule_query(schedule)
        schedule = Schedules().find_one(query)
        if schedule is None:
            raise ScheduleNotFound()
        else:
            return jsonify(schedule)

    @authenticate
    def patch(self, schedule: str, *args, **kwargs):
        """Update all properties of a schedule but _id and most_recent_task"""

        validator = t.Dict(
            t.Key("name", optional=True, trafaret=t.String(allow_blank=False)),
            t.Key("language", optional=True, trafaret=language_validator),
            t.Key("category", optional=True, trafaret=category_validator),
            t.Key("tags", optional=True, trafaret=t.List(t.String(allow_blank=False))),
            t.Key("enabled", optional=True, trafaret=t.Bool()),
            t.Key("config", optional=True, trafaret=config_validator),
        )

        try:
            update = validator.check(request.get_json())
            # empty dict passes the validator but troubles mongo
            if not request.get_json():
                raise t.DataError("Update can't be empty")
        except t.DataError as e:
            raise InvalidRequestJSON(str(e.error))

        if "name" in update:
            if Schedules().count_documents({"name": update["name"]}):
                raise BadRequest(
                    "Schedule with name `{}` already exists".format(update["name"])
                )

        query = self.get_schedule_query(schedule)
        matched_count = Schedules().update_one(query, {"$set": update}).matched_count

        if matched_count:
            return Response(status=HTTPStatus.NO_CONTENT)
        else:
            raise ScheduleNotFound()

    @authenticate
    def delete(self, schedule: str, *args, **kwargs):
        """Delete a schedule."""

        query = self.get_schedule_query(schedule)
        result = Schedules().delete_one(query)

        if result.deleted_count == 0:
            raise ScheduleNotFound()
        else:
            return Response(status=HTTPStatus.NO_CONTENT)
