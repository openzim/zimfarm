#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import logging
from http import HTTPStatus

import pymongo
from flask import request, jsonify, make_response, Response
from marshmallow import ValidationError

from common.enum import TaskStatus
from utils.token import AccessToken
from utils.broadcaster import BROADCASTER
from common.utils import task_event_handler
from common.mongo import RequestedTasks, Tasks
from errors.http import InvalidRequestJSON, TaskNotFound
from routes import authenticate, url_object_id, require_perm
from routes.base import BaseRoute
from common.schemas.parameters import TasksSchema, TaskCreateSchema, TasKUpdateSchema

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

    @url_object_id("task_id")
    def get(self, task_id: str):
        task = Tasks().find_one({"_id": task_id})
        if task is None:
            raise TaskNotFound()

        task["updated_at"] = task["events"][-1]["timestamp"]

        return jsonify(task)

    @authenticate
    @require_perm("tasks", "create")
    @url_object_id("task_id")
    def post(self, task_id: str, token: AccessToken.Payload):
        """ create a task from a requested_task_id """

        requested_task = RequestedTasks().find_one({"_id": task_id})
        if requested_task is None:
            raise TaskNotFound()

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
        if task is None:
            raise TaskNotFound()

        try:
            request_json = TasKUpdateSchema().load(request.get_json())
            # empty dict passes the validator but troubles mongo
            if not request.get_json():
                raise ValidationError("Update can't be empty")
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
        if task is None:
            raise TaskNotFound()

        task_event_handler(
            task["_id"], TaskStatus.cancel_requested, {"canceled_by": token.username}
        )

        # broadcast cancel-request to worker
        BROADCASTER.broadcast_cancel_task(task_id)

        return Response(status=HTTPStatus.NO_CONTENT)
