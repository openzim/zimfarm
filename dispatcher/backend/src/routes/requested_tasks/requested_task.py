import logging
import datetime
from http import HTTPStatus

import pytz
import pymongo
from flask import request, jsonify, make_response, Response
from marshmallow import Schema, fields, validate
from marshmallow.exceptions import ValidationError

from common.enum import TaskStatus, Offliner
from common.mongo import RequestedTasks, Schedules, Workers
from utils.offliners import command_information_for
from errors.http import InvalidRequestJSON, TaskNotFound
from routes import authenticate, url_object_id, auth_info_if_supplied
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

        class RequestArgsSchema(Schema):
            schedule_names = fields.List(
                fields.String(validate=validate.Length(min=5)), required=True
            )
            priority = fields.Integer(required=False, validate=validate.Range(min=0))
            worker = fields.String(required=False, validate=validate.Length(min=5))

        try:
            request_json = RequestArgsSchema().load(request.get_json())
        except ValidationError as e:
            raise InvalidRequestJSON(str(e.messages))

        schedule_names = request_json["schedule_names"]
        priority = request_json.get("priority", 0)
        worker = request_json.get("worker")

        # verify requested names exists
        if not Schedules().count_documents(
            {"name": {"$in": schedule_names}, "enabled": True}
        ) >= len(schedule_names):
            raise NotFound()

        try:
            username = kwargs["token"].username
        except Exception as exc:
            logger.error("unable to retrieve username from token")
            logger.exception(exc)
            username = None

        now = datetime.datetime.now(tz=pytz.utc)
        requested_tasks = []
        for schedule_name in schedule_names:

            # skip if already requested
            if RequestedTasks.count_documents(
                {"schedule_name": schedule_name, "worker": worker}
            ):
                continue

            schedule = Schedules().find_one(
                {"name": schedule_name, "enabled": True}, {"config": 1}
            )
            config = schedule.get("config")

            if not config:
                continue

            # build and save command-information to config
            config.update(command_information_for(config))

            document = {
                "schedule_name": schedule_name,
                "status": TaskStatus.requested,
                "timestamp": {TaskStatus.requested: now},
                "events": [{"code": TaskStatus.requested, "timestamp": now}],
                "requested_by": username,
                "priority": priority,
                "worker": worker,
                "config": config,
            }

            if worker:
                document["worker"] = worker

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

    @auth_info_if_supplied
    def get(self, *args, **kwargs):
        """ list of requested tasks """

        # validate query parameter
        class RequestArgsSchema(Schema):
            skip = fields.Integer(
                required=False, missing=0, validate=validate.Range(min=0)
            )
            limit = fields.Integer(
                required=False, missing=100, validate=validate.Range(min=0, max=200)
            )
            priority = fields.Integer(
                required=False, validate=validate.Range(min=0, max=10)
            )
            worker = fields.String(required=False)
            schedule_name = fields.String(
                required=False, validate=validate.Length(min=5)
            )
            matching_cpu = fields.Integer(
                required=False, validate=validate.Range(min=0)
            )
            matching_memory = fields.Integer(
                required=False, validate=validate.Range(min=0)
            )
            matching_disk = fields.Integer(
                required=False, validate=validate.Range(min=0)
            )
            matching_offliners = fields.List(
                fields.String(validate=validate.OneOf(Offliner.all())), required=False
            )

        request_args = request.args.to_dict()
        request_args["matching_offliners"] = request.args.getlist("matching_offliners")
        request_args = RequestArgsSchema().load(request_args)

        # unpack query parameter
        skip, limit = request_args["skip"], request_args["limit"]
        schedule_name = request_args.get("schedule_name")
        priority = request_args.get("priority")
        worker = request_args.get("worker")
        token = kwargs.get("token")

        # record we've seen a worker, if applicable
        if token and worker:
            Workers().update_one(
                {"name": worker, "username": token.username},
                {"$set": {"last_seen": datetime.datetime.now()}},
            )

        # get requested tasks from database
        query = {}
        if schedule_name:
            query["schedule_name"] = schedule_name

        if priority:
            query["priority"] = {"$gte": priority}

        if worker:
            query["worker"] = {"$in": [None, worker]}

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
                    "schedule_name": 1,
                    "config.task_name": 1,
                    "config.resources": 1,
                    "timestamp.requested": 1,
                    "requested_by": 1,
                    "priority": 1,
                    "worker": 1,
                },
            )
            .sort(
                [
                    ("priority", pymongo.DESCENDING),
                    ("timestamp.requested", pymongo.DESCENDING),
                ]
            )
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
    methods = ["GET", "PATCH", "DELETE"]

    @url_object_id("requested_task_id")
    def get(self, requested_task_id: str, *args, **kwargs):

        requested_task = RequestedTasks().find_one({"_id": requested_task_id})
        if requested_task is None:
            raise TaskNotFound()

        return jsonify(requested_task)

    @url_object_id("requested_task_id")
    def patch(self, requested_task_id: str, *args, **kwargs):

        requested_task = RequestedTasks().count_documents({"_id": requested_task_id})
        if not requested_task:
            raise TaskNotFound()

        class JsonRequestSchema(Schema):
            priority = fields.Integer(
                required=True, validate=validate.Range(min=0, max=10)
            )

        try:
            request_json = JsonRequestSchema().load(request.get_json())
        except ValidationError as e:
            raise InvalidRequestJSON(str(e.messages))

        update = RequestedTasks().update_one(
            {"_id": requested_task_id},
            {"$set": {"priority": request_json.get("priority", 0)}},
        )
        if update.modified_count:
            return Response(status=HTTPStatus.ACCEPTED)
        return Response(status=HTTPStatus.OK)

    @authenticate
    @url_object_id("requested_task_id")
    def delete(self, requested_task_id: str, *args, **kwargs):

        query = {"_id": requested_task_id}
        task = RequestedTasks().find_one(query, {"_id": 1})
        if task is None:
            raise TaskNotFound()

        result = RequestedTasks().delete_one(query)
        return jsonify({"deleted": result.deleted_count})
