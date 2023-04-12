import datetime
import logging
from http import HTTPStatus

import pymongo
from bson import ObjectId
from flask import Response, jsonify, make_response, request
from marshmallow import ValidationError

from common import WorkersIpChangesCounts, getnow
from common.constants import (
    ENABLED_SCHEDULER,
    MAX_WORKER_IP_CHANGES_PER_DAY,
    USES_WORKERS_IPS_WHITELIST,
)
from common.external import update_workers_whitelist
from common.mongo import RequestedTasks, Schedules, Workers
from common.schemas.parameters import (
    NewRequestedTaskSchema,
    RequestedTaskSchema,
    UpdateRequestedTaskSchema,
    WorkerRequestedTaskSchema,
)
from common.utils import task_event_handler
from errors.http import InvalidRequestJSON, TaskNotFound
from routes import auth_info_if_supplied, authenticate, require_perm, url_object_id
from routes.base import BaseRoute
from routes.errors import NotFound
from routes.utils import raise_if, raise_if_none
from utils.broadcaster import BROADCASTER
from utils.scheduling import find_requested_task_for, request_a_schedule
from utils.token import AccessToken

logger = logging.getLogger(__name__)


def record_ip_change(worker_name):
    """record that this worker changed its IP and trigger whitelist changes"""
    today = datetime.date.today()
    # counts and limits are per-day so reset it if date changed
    if today != WorkersIpChangesCounts.today:
        WorkersIpChangesCounts.reset()
    if WorkersIpChangesCounts.add(worker_name) <= MAX_WORKER_IP_CHANGES_PER_DAY:
        update_workers_whitelist()
    else:
        logger.error(
            f"Worker {worker_name} IP changes for {today} "
            f"is above limit ({MAX_WORKER_IP_CHANGES_PER_DAY}). Not updating whitelist!"
        )


def list_of_requested_tasks(token: AccessToken.Payload = None):
    """list of requested tasks"""

    request_args = request.args.to_dict()
    worker = request_args.get("worker")

    # record we've seen a worker, if applicable
    if token and worker:
        Workers().update_one(
            {"name": worker, "username": token.username},
            {"$set": {"last_seen": getnow()}},
        )

    request_args["matching_offliners"] = request.args.getlist("matching_offliners")
    request_args["schedule_name"] = request.args.getlist("schedule_name")
    request_args = RequestedTaskSchema().load(request_args)

    # unpack query parameter
    skip, limit = request_args["skip"], request_args["limit"]
    schedule_names = request_args["schedule_name"]
    priority = request_args.get("priority")

    # get requested tasks from database
    query = {}
    if schedule_names:
        query["schedule_name"] = {"$in": schedule_names}

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
                ("timestamp.reserved", pymongo.DESCENDING),
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


class RequestedTasksRoute(BaseRoute):
    rule = "/"
    name = "requested_tasks"
    methods = ["POST", "GET"]

    @authenticate
    @require_perm("tasks", "request")
    def post(self, token: AccessToken.Payload):
        """Create requested task from a list of schedule_names"""

        try:
            request_json = NewRequestedTaskSchema().load(request.get_json())
        except ValidationError as e:
            raise InvalidRequestJSON(e.messages)

        schedule_names = request_json["schedule_names"]
        priority = request_json.get("priority", 0)
        worker = request_json.get("worker")

        # raise 404 if nothing to schedule
        if not Schedules().count_documents(
            {"name": {"$in": schedule_names}, "enabled": True}
        ):
            raise NotFound()

        requested_tasks = []
        for schedule_name in schedule_names:
            rq_task = request_a_schedule(
                schedule_name, token.username, worker, priority
            )
            if rq_task is None:
                continue

            requested_tasks.append(rq_task)

        if len(requested_tasks) > 1:
            BROADCASTER.broadcast_requested_tasks(requested_tasks)
        elif len(requested_tasks) == 1:
            BROADCASTER.broadcast_requested_task(requested_tasks[0])

        # trigger event handler
        for task in requested_tasks:
            task_event_handler(ObjectId(task["_id"]), "requested", {})

        return make_response(
            jsonify({"requested": [rt["_id"] for rt in requested_tasks]}),
            HTTPStatus.CREATED,
        )

    @auth_info_if_supplied
    def get(self, token: AccessToken.Payload = None):
        """list of requested tasks for API users, no-auth"""
        return list_of_requested_tasks(token)


class RequestedTasksForWorkers(BaseRoute):
    rule = "/worker"
    name = "requested_tasks_workers"
    methods = ["GET"]

    @authenticate
    def get(self, token: AccessToken.Payload):
        """list of requested tasks to be retrieved by workers, auth-only"""

        if not ENABLED_SCHEDULER:
            return jsonify(
                {
                    "meta": {"skip": 0, "limit": 1, "count": 0},
                    "items": [],
                }
            )

        request_args = request.args.to_dict()
        worker_name = request_args.get("worker")
        worker_ip = request.headers.get("X-Forwarded-For", request.remote_addr)

        worker_query = {"name": worker_name, "username": token.username}
        last_ip = Workers().find_one(worker_query, {"last_ip": 1}).get("last_ip")

        # record we've seen a worker, if applicable
        if token and worker_name:
            Workers().update_one(
                {"name": worker_name, "username": token.username},
                {"$set": {"last_seen": getnow(), "last_ip": worker_ip}},
            )

        # IP changed since last encounter
        if USES_WORKERS_IPS_WHITELIST and last_ip != worker_ip:
            record_ip_change(worker_name)

        request_args = WorkerRequestedTaskSchema().load(request_args)

        task = find_requested_task_for(
            token.username,
            worker_name,
            request_args["avail_cpu"],
            request_args["avail_memory"],
            request_args["avail_disk"],
        )

        return jsonify(
            {
                "meta": {"skip": 0, "limit": 1, "count": 1 if task else 0},
                "items": [task] if task else [],
            }
        )


class RequestedTaskRoute(BaseRoute):
    rule = "/<string:requested_task_id>"
    name = "requested_task"
    methods = ["GET", "PATCH", "DELETE"]

    @url_object_id("requested_task_id")
    def get(self, requested_task_id: str):
        requested_task = RequestedTasks().find_one({"_id": requested_task_id})
        raise_if_none(requested_task, TaskNotFound())

        return jsonify(requested_task)

    @authenticate
    @require_perm("tasks", "update")
    @url_object_id("requested_task_id")
    def patch(self, requested_task_id: str, token: AccessToken.Payload):
        requested_task = RequestedTasks().count_documents({"_id": requested_task_id})
        raise_if(not requested_task, TaskNotFound())

        try:
            request_json = UpdateRequestedTaskSchema().load(request.get_json())
        except ValidationError as e:
            raise InvalidRequestJSON(e.messages)

        update = RequestedTasks().update_one(
            {"_id": requested_task_id},
            {"$set": {"priority": request_json.get("priority", 0)}},
        )
        if update.modified_count:
            return Response(status=HTTPStatus.ACCEPTED)
        return Response(status=HTTPStatus.OK)

    @authenticate
    @require_perm("tasks", "unrequest")
    @url_object_id("requested_task_id")
    def delete(self, requested_task_id: str, token: AccessToken.Payload):
        query = {"_id": requested_task_id}
        task = RequestedTasks().find_one(query, {"_id": 1})
        raise_if_none(task, TaskNotFound())

        result = RequestedTasks().delete_one(query)
        return jsonify({"deleted": result.deleted_count})
