#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import logging
from http import HTTPStatus

import pymongo
from flask import Response, jsonify, make_response, request
from marshmallow import ValidationError

from common.constants import ENABLED_SCHEDULER
from common.enum import TaskStatus
from common.mongo import RequestedTasks, Tasks
from common.schemas.parameters import TaskCreateSchema, TasksSchema, TasKUpdateSchema
from common.utils import task_event_handler
from errors.http import InvalidRequestJSON, TaskNotFound
from routes import auth_info_if_supplied, authenticate, require_perm, url_object_id
from routes.base import BaseRoute
from routes.utils import raise_if, raise_if_none, remove_secrets_from_response
from utils.broadcaster import BROADCASTER
from utils.token import AccessToken

logger = logging.getLogger(__name__)


class TasksRoute(BaseRoute):
    rule = "/"
    name = "tasks"
    methods = ["GET"]

    def get(self):
        """Return a list of tasks"""

        request_args = request.args.to_dict()
        request_args["status"] = request.args.getlist("status")
        request_args = TasksSchema().load(request_args)

        # unpack query parameter
        skip, limit = request_args["skip"], request_args["limit"]
        statuses = request_args.get("status")
        schedule_name = request_args.get("schedule_name")

        # get tasks from database
        query = {}
        if statuses:
            query["status"] = {"$in": statuses}
        if schedule_name:
            query["schedule_name"] = schedule_name

        count = Tasks().count_documents(query)

        cursor = Tasks().aggregate(
            [
                {"$match": query},
                {
                    "$project": {
                        "schedule_name": 1,
                        "status": 1,
                        "timestamp": 1,
                        "worker": 1,
                        "config.resources": 1,
                        "updated_at": {"$arrayElemAt": ["$events.timestamp", -1]},
                    }
                },
                {"$sort": {"updated_at": pymongo.DESCENDING}},
                {"$skip": skip},
                {"$limit": limit},
            ]
        )

        tasks = list(cursor)

        return jsonify(
            {"meta": {"skip": skip, "limit": limit, "count": count}, "items": tasks}
        )


class TaskRoute(BaseRoute):
    rule = "/<string:task_id>"
    name = "task"
    methods = ["GET", "POST", "PATCH"]

    @auth_info_if_supplied
    @url_object_id("task_id")
    def get(self, task_id: str, token: AccessToken.Payload = None):
        # exclude notification to not expose private information (privacy)
        # on anonymous requests and requests for users without schedules_update
        projection = (
            None
            if token and token.get_permission("schedules", "update")
            else {"notification": 0}
        )

        task = Tasks().find_one({"_id": task_id}, projection)
        raise_if_none(task, TaskNotFound)

        task["updated_at"] = task["events"][-1]["timestamp"]

        if not token or not token.get_permission("tasks", "create"):
            remove_secrets_from_response(task)

        return jsonify(task)

    @authenticate
    @require_perm("tasks", "create")
    @url_object_id("task_id")
    def post(self, task_id: str, token: AccessToken.Payload):
        """create a task from a requested_task_id"""

        if not ENABLED_SCHEDULER:
            raise make_response(
                jsonify({"msg": "scheduler is paused"}), HTTPStatus.NO_CONTENT
            )

        requested_task = RequestedTasks().find_one({"_id": task_id})
        raise_if_none(requested_task, TaskNotFound)

        request_args = TaskCreateSchema().load(request.args.to_dict())

        document = {}
        document.update(requested_task)

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

        payload = {"worker": request_args["worker_name"]}
        try:
            task_event_handler(task_id, TaskStatus.reserved, payload)
        except Exception as exc:
            logger.exception(exc)
            logger.error("unable to create task. reverting.")
            try:
                Tasks().delete_one({"_id": task_id})
            except Exception:
                logger.debug(f"unable to revert deletion of task {task_id}")
            raise exc

        try:
            RequestedTasks().delete_one({"_id": task_id})
        except Exception as exc:
            logger.exception(exc)  # and pass

        BROADCASTER.broadcast_updated_task(task_id, TaskStatus.reserved, payload)

        return make_response(
            jsonify(Tasks().find_one({"_id": task_id})), HTTPStatus.CREATED
        )

    @authenticate
    @require_perm("tasks", "update")
    @url_object_id("task_id")
    def patch(self, task_id: str, token: AccessToken.Payload):
        task = Tasks().find_one({"_id": task_id}, {"_id": 1})
        raise_if_none(task, TaskNotFound)

        try:
            request_json = TasKUpdateSchema().load(request.get_json())
            # empty dict passes the validator but troubles mongo
            raise_if(not request.get_json(), ValidationError, "Update can't be empty")
        except ValidationError as e:
            raise InvalidRequestJSON(e.messages)

        task_event_handler(task["_id"], request_json["event"], request_json["payload"])

        BROADCASTER.broadcast_updated_task(
            task_id, request_json["event"], request_json["payload"]
        )

        return Response(status=HTTPStatus.NO_CONTENT)


class TaskCancelRoute(BaseRoute):
    rule = "/<string:task_id>/cancel"
    name = "task_cancel"
    methods = ["POST"]

    @authenticate
    @require_perm("tasks", "cancel")
    @url_object_id("task_id")
    def post(self, task_id: str, token: AccessToken.Payload):
        task = Tasks().find_one(
            {"status": {"$in": TaskStatus.incomplete()}, "_id": task_id}, {"_id": 1}
        )
        raise_if_none(task, TaskNotFound)

        task_event_handler(
            task["_id"], TaskStatus.cancel_requested, {"canceled_by": token.username}
        )

        # broadcast cancel-request to worker
        BROADCASTER.broadcast_cancel_task(task_id)

        return Response(status=HTTPStatus.NO_CONTENT)
