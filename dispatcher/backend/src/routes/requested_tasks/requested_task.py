import logging
import datetime
from http import HTTPStatus

import pytz
import pymongo
import trafaret as t
from flask import request, jsonify, make_response

from common.entities import TaskStatus
from common.mongo import RequestedTasks, Schedules
from utils.offliners import command_information_for
from errors.http import InvalidRequestJSON, TaskNotFound
from routes import authenticate, url_object_id
from routes.base import BaseRoute
from routes.errors import NotFound
from utils.broadcaster import BROADCASTER

logger = logging.getLogger(__name__)


class RequestedTasksRoute(BaseRoute):
    rule = "/"
    name = "requested_tasks"
    methods = ["POST", "GET"]

    @authenticate
    def post(self, *args, **kwargs):
        """ Create requested task from a list of schedule_names """

        request_json = request.get_json()
        if not request_json:
            raise InvalidRequestJSON()
        schedule_names = request_json.get("schedule_names", [])
        if not isinstance(schedule_names, list):
            raise InvalidRequestJSON()

        # verify requested names exists
        if not Schedules().count_documents(
            {"name": {"$in": schedule_names}, "enabled": True}
        ) >= len(schedule_names):
            raise NotFound()

        now = datetime.datetime.now(tz=pytz.utc)
        requested_tasks = []
        for schedule_name in schedule_names:

            schedule = Schedules().find_one(
                {"name": schedule_name, "enabled": True}, {"config": 1}
            )
            config = schedule.get("config")

            if not config:
                continue

            # build and save command-information to config
            config.update(command_information_for(config))

            document = {
                "schedule_id": schedule["_id"],
                "schedule_name": schedule_name,
                "status": TaskStatus.requested,
                "timestamp": {TaskStatus.requested: now},
                "events": [{"code": TaskStatus.requested, "timestamp": now}],
                "config": config,
            }

            rt_id = RequestedTasks().insert_one(document).inserted_id
            document.update({"_id": str(rt_id)})
            requested_tasks.append(document)

        if len(requested_tasks) > 1:
            BROADCASTER.broadcast_requested_tasks(requested_tasks)
        elif len(requested_tasks) == 1:
            BROADCASTER.broadcast_requested_task(requested_tasks[0])

        return make_response(
            jsonify({"requested": [rt["_id"] for rt in requested_tasks]}),
            HTTPStatus.CREATED,
        )

    def get(self, *args, **kwargs):
        """ list of requested tasks """

        # validate query parameter
        request_args = request.args.to_dict()
        request_args["matching_offliners"] = request.args.getlist("matching_offliners")

        validator = t.Dict(
            {
                t.Key("skip", default=0): t.ToInt(gte=0),
                t.Key("limit", default=100): t.ToInt(gt=0, lte=200),
                t.Key("schedule_name", optional=True): t.String(),
                t.Key("matching_cpu", optional=True): t.ToInt(gte=0),
                t.Key("matching_memory", optional=True): t.ToInt(gte=0),
                t.Key("matching_disk", optional=True): t.ToInt(gte=0),
                t.Key("matching_offliners", optional=True): t.List(
                    t.Enum("mwoffliner", "youtube", "gutenberg", "ted", "phet")
                ),
            }
        )
        request_args = validator.check(request_args)

        # unpack query parameter
        skip, limit = request_args["skip"], request_args["limit"]
        schedule_name = request_args.get("schedule_name")

        # get requested tasks from database
        query = {}
        if schedule_name:
            query["schedule_name"] = schedule_name

        for res_key in ("cpu", "memory", "disk"):
            key = f"matching_{res_key}"
            if key in request_args:
                query[f"config.resources.{res_key}"] = {"$lte": request_args[key]}
        matching_offliners = request_args.get("matching_offliners")
        if matching_offliners:
            query["config.task_name"] = {"$in": matching_offliners}

        cursor = (
            RequestedTasks()
            .find(
                query,
                {
                    "_id": 1,
                    "status": 1,
                    "schedule_id": 1,
                    "schedule_name": 1,
                    "config.task_name": 1,
                    "config.resources": 1,
                    "timestamp.requested": 1,
                },
            )
            .sort("timestamp.requested", pymongo.DESCENDING)
            .skip(skip)
            .limit(limit)
        )
        count = RequestedTasks().count_documents(query)

        return jsonify(
            {
                "meta": {"skip": skip, "limit": limit, "count": count},
                "items": [task for task in cursor],
            }
        )


class RequestedTaskRoute(BaseRoute):
    rule = "/<string:requested_task_id>"
    name = "requested_task"
    methods = ["GET"]

    @url_object_id("requested_task_id")
    def get(self, requested_task_id: str, *args, **kwargs):

        requested_task = RequestedTasks().find_one({"_id": requested_task_id})
        if requested_task is None:
            raise TaskNotFound()

        return jsonify(requested_task)


class RequestedTaskDeleteRoute(BaseRoute):
    rule = "/<string:requested_task_id>"
    name = "requested_task_delete"
    methods = ["DELETE"]

    @authenticate
    @url_object_id("requested_task_id")
    def delete(self, requested_task_id: str, *args, **kwargs):

        query = {"_id": requested_task_id}
        task = RequestedTasks().find_one(query, {"_id": 1})
        if task is None:
            raise TaskNotFound()

        result = RequestedTasks().delete_one(query)
        return jsonify({"deleted": result.deleted_count})
