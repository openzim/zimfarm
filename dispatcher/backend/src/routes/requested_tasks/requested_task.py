import datetime
import logging
from http import HTTPStatus
from uuid import UUID

import sqlalchemy as sa
import sqlalchemy.orm as so
from flask import Response, jsonify, make_response, request
from marshmallow import ValidationError

import db.models as dbm
from common import WorkersIpChangesCounts, getnow
from common.constants import (
    ENABLED_SCHEDULER,
    MAX_WORKER_IP_CHANGES_PER_DAY,
    USES_WORKERS_IPS_WHITELIST,
)
from common.external import update_workers_whitelist
from common.schemas.orms import RequestedTaskFullSchema, RequestedTaskLightSchema
from common.schemas.parameters import (
    NewRequestedTaskSchema,
    RequestedTaskSchema,
    UpdateRequestedTaskSchema,
    WorkerRequestedTaskSchema,
)
from common.utils import task_event_handler
from db import count_from_stmt, dbsession, dbsession_manual
from errors.http import InvalidRequestJSON, TaskNotFound, WorkerNotFound, HTTPBase
from routes import auth_info_if_supplied, authenticate, require_perm, url_uuid
from routes.base import BaseRoute
from routes.errors import NotFound
from utils.scheduling import find_requested_task_for, request_a_schedule
from utils.token import AccessToken

logger = logging.getLogger(__name__)


def record_ip_change(session: so.Session, worker_name: str):
    """record that this worker changed its IP and trigger whitelist changes"""
    today = datetime.date.today()
    # counts and limits are per-day so reset it if date changed
    if today != WorkersIpChangesCounts.today:
        WorkersIpChangesCounts.reset()
    if WorkersIpChangesCounts.add(worker_name) <= MAX_WORKER_IP_CHANGES_PER_DAY:
        update_workers_whitelist(session)
    else:
        logger.error(
            f"Worker {worker_name} IP changes for {today} "
            f"is above limit ({MAX_WORKER_IP_CHANGES_PER_DAY}). Not updating whitelist!"
        )


@dbsession
def list_of_requested_tasks(session: so.Session, token: AccessToken.Payload = None):
    """list of requested tasks"""

    request_args = request.args.to_dict()
    worker = request_args.get("worker")

    # record we've seen a worker, if applicable
    if token and worker:
        worker = dbm.Worker.get(session, worker, WorkerNotFound)
        if worker.user.username == token.username:
            worker.last_seen = getnow()

    request_args["matching_offliners"] = request.args.getlist("matching_offliners")
    request_args["schedule_name"] = request.args.getlist("schedule_name")
    request_args = RequestedTaskSchema().load(request_args)

    # unpack query parameter
    skip, limit = request_args["skip"], request_args["limit"]
    schedule_names = request_args["schedule_name"]
    priority = request_args.get("priority")

    # get requested tasks from database
    stmt = (
        sa.select(
            dbm.RequestedTask.id,
            dbm.RequestedTask.status,
            so.Bundle(
                "config",
                dbm.RequestedTask.config["task_name"].label("task_name"),
                dbm.RequestedTask.config["resources"].label("resources"),
            ),
            dbm.RequestedTask.timestamp,
            dbm.RequestedTask.requested_by,
            dbm.RequestedTask.priority,
            dbm.RequestedTask.original_schedule_name,
            dbm.Schedule.name.label("schedule_name"),
            dbm.Worker.name.label("worker"),
        )
        .join(dbm.Worker, dbm.RequestedTask.worker, isouter=True)
        .join(dbm.Schedule, dbm.RequestedTask.schedule, isouter=True)
        .order_by(dbm.RequestedTask.priority.desc())
        .order_by(
            dbm.RequestedTask.timestamp["reserved"]["$date"].astext.cast(sa.BigInteger)
        )
        .order_by(
            dbm.RequestedTask.timestamp["requested"]["$date"].astext.cast(sa.BigInteger)
        )
    )

    if schedule_names:
        stmt = stmt.filter(dbm.Schedule.name.in_(schedule_names))

    if priority:
        stmt = stmt.filter(dbm.RequestedTask.priority >= priority)

    if worker:
        stmt = stmt.filter(
            sa.or_(
                dbm.RequestedTask.worker == None,  # noqa: E711
                dbm.Worker.name == worker,
            )
        )

    for res_key in ("cpu", "memory", "disk"):
        key = f"matching_{res_key}"
        if key in request_args:
            stmt = stmt.filter(
                dbm.RequestedTask.config["resources"][res_key].astext.cast(
                    sa.BigInteger
                )
                <= request_args[key]
            )
    matching_offliners = request_args.get("matching_offliners")
    if matching_offliners:
        stmt = stmt.filter(
            dbm.RequestedTask.config["task_name"].astext.in_(matching_offliners)
        )

    count = count_from_stmt(session, stmt)

    return jsonify(
        {
            "meta": {"skip": skip, "limit": limit, "count": count},
            "items": list(
                map(
                    RequestedTaskLightSchema().dump,
                    session.execute(stmt.offset(skip).limit(limit)).all(),
                )
            ),
        }
    )


class RequestedTasksRoute(BaseRoute):
    rule = "/"
    name = "requested_tasks"
    methods = ["POST", "GET"]

    @authenticate
    @require_perm("tasks", "request")
    @dbsession
    def post(self, session: so.Session, token: AccessToken.Payload):
        """Create requested task from a list of schedule_names"""

        try:
            request_json = NewRequestedTaskSchema().load(request.get_json())
        except ValidationError as e:
            raise InvalidRequestJSON(e.messages)

        schedule_names = request_json["schedule_names"]
        priority = request_json.get("priority", 0)
        worker = request_json.get("worker")

        # raise 404 if nothing to schedule
        if not count_from_stmt(
            session=session,
            stmt=sa.select(dbm.Schedule)
            .filter(dbm.Schedule.name.in_(schedule_names))
            .filter(dbm.Schedule.enabled),
        ):
            raise NotFound()

        requested_tasks = []
        for schedule_name in schedule_names:
            rq_task = request_a_schedule(
                session=session,
                schedule_name=schedule_name,
                requested_by=token.username,
                worker_name=worker,
                priority=priority,
            )
            if rq_task is None:
                continue

            requested_tasks.append(rq_task)

        # trigger event handler
        for task in requested_tasks:
            task_event_handler(session, task["_id"], "requested", {})

        return make_response(
            jsonify({"requested": [task["_id"] for task in requested_tasks]}),
            HTTPStatus.CREATED,
        )

    @auth_info_if_supplied
    def get(self, token: AccessToken.Payload = None):
        """list of requested tasks for API users, no-auth"""
        return list_of_requested_tasks(token=token)


class RequestedTasksForWorkers(BaseRoute):
    rule = "/worker"
    name = "requested_tasks_workers"
    methods = ["GET"]

    @authenticate
    @dbsession_manual
    def get(self, session: so.Session, token: AccessToken.Payload):
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

        # record we've seen a worker, if applicable
        if token and worker_name:
            worker = dbm.Worker.get(session, worker_name, WorkerNotFound)
            if worker.user.username == token.username:
                worker.last_seen = getnow()

                # IP changed since last encounter
                if str(worker.last_ip) != worker_ip:
                    logger.info(
                        f"Worker IP changed detected for {worker_name}: "
                        f"IP changed from {worker.last_ip} to {worker_ip}"
                    )
                    worker.last_ip = worker_ip
                    # commit explicitely since we are not using an explicit transaction,
                    # and do it before calling Wasabi so that changes are propagated
                    # quickly and transaction is not blocking
                    session.commit()
                    if constants.USES_WORKERS_IPS_WHITELIST:
                        try:
                            record_ip_change(session=session, worker_name=worker_name)
                        except Exception:
                            raise HTTPBase(
                                status_code=HTTPStatus.SERVICE_UNAVAILABLE,
                                error="Recording IP changes failed",
                            )

        request_args = WorkerRequestedTaskSchema().load(request_args)

        task = find_requested_task_for(
            session=session,
            username=token.username,
            worker_name=worker_name,
            avail_cpu=request_args["avail_cpu"],
            avail_memory=request_args["avail_memory"],
            avail_disk=request_args["avail_disk"],
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

    @url_uuid("requested_task_id")
    @dbsession
    def get(self, session: so.Session, requested_task_id: UUID):
        requested_task = dbm.RequestedTask.get(session, requested_task_id, TaskNotFound)
        resp = RequestedTaskFullSchema().dump(requested_task)
        return jsonify(resp)

    @authenticate
    @require_perm("tasks", "update")
    @url_uuid("requested_task_id")
    @dbsession
    def patch(
        self, session: so.Session, requested_task_id: UUID, token: AccessToken.Payload
    ):
        requested_task = dbm.RequestedTask.get(session, requested_task_id, TaskNotFound)

        try:
            request_json = UpdateRequestedTaskSchema().load(request.get_json())
        except ValidationError as e:
            raise InvalidRequestJSON(e.messages)

        requested_task.priority = request_json.get("priority", 0)

        return Response(status=HTTPStatus.NO_CONTENT)

    @authenticate
    @require_perm("tasks", "unrequest")
    @url_uuid("requested_task_id")
    @dbsession
    def delete(
        self, session: so.Session, requested_task_id: UUID, token: AccessToken.Payload
    ):
        requested_task = dbm.RequestedTask.get(session, requested_task_id, TaskNotFound)
        session.delete(requested_task)

        return jsonify({"deleted": 1})
