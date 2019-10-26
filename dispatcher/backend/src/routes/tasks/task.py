#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import logging
import datetime

import pytz
import pymongo
import trafaret as t
from bson.objectid import ObjectId, InvalidId
from flask import request, jsonify

from common.entities import TaskStatus
from utils.broadcaster import BROADCASTER
from common.utils import task_event_handler
from common.mongo import RequestedTasks, Tasks
from errors.http import InvalidRequestJSON, TaskNotFound
from routes import authenticate
from routes.base import BaseRoute
from common.validators import ObjectIdValidator

logger = logging.getLogger(__name__)


class TasksRoute(BaseRoute):
    rule = "/"
    name = "tasks"
    methods = ["GET"]

    @authenticate
    def get(self, *args, **kwargs):
        """Return a list of tasks"""

        # validate query parameter
        request_args = request.args.to_dict()
        request_args["status"] = request.args.getlist("status")
        validator = t.Dict(
            {
                t.Key("skip", default=0): t.Int(gte=0),
                t.Key("limit", default=100): t.Int(gt=0, lte=200),
                t.Key("status", optional=True): t.List(t.Enum(*TaskStatus.all())),
                t.Key("schedule_id", optional=True): ObjectIdValidator,
            }
        )
        request_args = validator.check(request_args)

        # unpack query parameter
        skip, limit = request_args["skip"], request_args["limit"]
        statuses = request_args.get("status")
        schedule_id = request_args.get("schedule_id")

        # get tasks from database
        if statuses:
            query = {"status": {"$in": statuses}}
        else:
            query = {"status": {"$nin": ["sent", "received"]}}
        if schedule_id:
            query["schedule._id"] = schedule_id

        count = Tasks.count_documents(query)
        projection = {"_id": 1, "status": 1, "timestamp.requested": 1, "schedule": 1}
        cursor = (
            Tasks()
            .find(query, projection)
            .sort("timestamp.requested", pymongo.DESCENDING)
            .skip(skip)
            .limit(limit)
        )
        tasks = [task for task in cursor]

        return jsonify(
            {"meta": {"skip": skip, "limit": limit, "count": count}, "items": tasks}
        )


class TaskRoute(BaseRoute):
    rule = "/<string:task_id>"
    name = "task"
    methods = ["GET", "POST", "PATCH"]

    @authenticate
    def get(self, task_id: str, *args, **kwargs):
        try:
            task_id = ObjectId(task_id)
        except InvalidId:
            task_id = None

        task = Tasks().find_one({"_id": task_id})
        if task is None:
            raise TaskNotFound()
        else:
            return jsonify(task)

    @authenticate
    def post(self, task_id: str, *args, **kwargs):
        """ create a task from a requested_task_id """
        try:
            task_id = ObjectId(task_id)
        except InvalidId:
            task_id = None

        requested_task = RequestedTasks().find_one({"_id": task_id})
        if requested_task is None:
            raise TaskNotFound()

        worker_name = request.args.get("worker_name")
        if not worker_name:
            raise InvalidRequestJSON("missing worker_name")

        now = datetime.datetime.now(tz=pytz.utc)

        document = {}
        document.update(requested_task)
        # document.update({"status": TaskStatus.started, "worker": worker_name})
        # document["timestamp"].update({TaskStatus.started: now})
        # document["events"].append({"code": TaskStatus.started, "timestamp": now})

        try:
            Tasks().insert_one(requested_task)
        except pymongo.errors.DuplicateKeyError as exc:
            logger.exception(exc)
            response = jsonify({})
            response.status_code = 423  # Locked
            return response
        except Exception as exc:
            logger.exception(exc)
            raise exc

        try:
            task_event_handler(
                task_id,
                TaskStatus.started,
                {"worker": worker_name, "timestamp": now.isoformat()},
            )
        except Exception as exc:
            logger.exception(exc)
            logger.error("unable to create task. reverting.")
            try:
                Tasks().delete_one({"_id": task_id})
            except Exception:
                pass
            raise exc

        try:
            RequestedTasks().delete_one({"_id": task_id})
            pass
        except Exception as exc:
            logger.exception(exc)  # and pass

        response = jsonify(Tasks().find_one({"_id": task_id}))
        response.status_code = 201
        return response

    @authenticate
    def patch(self, task_id: str, *args, **kwargs):
        try:
            task_id = ObjectId(task_id)
        except InvalidId:
            task_id = None

        task = Tasks().find_one({"_id": task_id}, {"_id": 1})
        if task is None:
            raise TaskNotFound()

        # only applies to started tasks
        events = TaskStatus.all() + TaskStatus.file_events()
        events.remove(TaskStatus.requested)
        events.remove(TaskStatus.started)

        validator = t.Dict(
            t.Key("event", optional=False, trafaret=t.Enum(*events)),
            t.Key("payload", optional=False, trafaret=t.Dict({}, allow_extra=["*"])),
        )

        try:
            from pprint import pprint as pp

            pp(request.get_json())
            payload = validator.check(request.get_json())
            # empty dict passes the validator but troubles mongo
            if not request.get_json():
                raise t.DataError("Update can't be empty")
        except t.DataError as e:
            raise InvalidRequestJSON(str(e.error))

        result = task_event_handler(task["_id"], payload["event"], payload["payload"])

        return jsonify(result)


class TaskCancelRoute(BaseRoute):
    rule = "/<string:task_id>/cancel"
    name = "task_cancel"
    methods = ["POST"]

    @authenticate
    def post(self, task_id: str, *args, **kwargs):

        try:
            task_id = ObjectId(task_id)
        except InvalidId:
            task_id = None

        task = Tasks().find_one(
            {"status": {"$in": TaskStatus.incomplete()}, "_id": task_id}, {"_id": 1}
        )
        if task is None:
            raise TaskNotFound()

        result = task_event_handler(task["_id"], TaskStatus.cancelled, {})

        # broadcast cancel-request to worker
        BROADCASTER.broadcast_cancel_task(task_id)

        return jsonify(result)
