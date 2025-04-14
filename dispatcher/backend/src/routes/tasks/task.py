#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import logging
from http import HTTPStatus
from uuid import UUID

import sqlalchemy as sa
import sqlalchemy.orm as so
from flask import Response, jsonify, make_response, request
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError

import db.models as dbm
from common.constants import ENABLED_SCHEDULER
from common.enum import TaskStatus
from common.schemas.orms import TaskFullSchema, TaskLightSchema
from common.schemas.parameters import TaskCreateSchema, TasksSchema, TasKUpdateSchema
from common.utils import task_event_handler
from db import count_from_stmt, dbsession
from errors.http import InvalidRequestJSON, TaskNotFound, WorkerNotFound
from routes import auth_info_if_supplied, authenticate, require_perm, url_uuid
from routes.base import BaseRoute
from routes.errors import BadRequest
from routes.utils import get_sort_field_and_apply_order, remove_secrets_from_response
from utils.check import raise_if, raise_if_none
from utils.token import AccessToken

logger = logging.getLogger(__name__)


class TasksRoute(BaseRoute):
    rule = "/"
    name = "tasks"
    methods = ["GET"]

    @dbsession
    def get(self, session: so.Session):
        """Return a list of tasks"""

        request_args = request.args.to_dict()
        request_args["status"] = request.args.getlist("status")
        request_args = TasksSchema().load(request_args)

        # unpack query parameter
        skip, limit = request_args["skip"], request_args["limit"]
        statuses = request_args.get("status")
        schedule_name = request_args.get("schedule_name")
        # Get sorting parameters
        sort_by = request_args.get("sort_by")
        sort_order = request_args.get("sort_order", "desc")

        stmt = (
            sa.select(
                dbm.Task.id,
                dbm.Task.status,
                dbm.Task.timestamp,
                dbm.Task.original_schedule_name,
                # dbm.Task.config,
                so.Bundle(
                    "config",
                    dbm.Task.config["resources"].label("resources"),
                ),
                dbm.Task.updated_at,
                dbm.Schedule.name.label("schedule_name"),
                dbm.Worker.name.label("worker_name"),
            )
            .join(dbm.Worker, dbm.Task.worker, isouter=True)
            .join(dbm.Schedule, dbm.Task.schedule, isouter=True)
        )
        join_models = {"Schedule": dbm.Schedule, "Worker": dbm.Worker}
        default_field = dbm.Task.updated_at
        stmt = get_sort_field_and_apply_order(
            model=dbm.Task,
            sort_by=sort_by,
            sort_order=sort_order,
            stmt=stmt,
            join_models=join_models,
            fallback_field=default_field,
        )

        # get tasks from database
        if statuses:
            stmt = stmt.filter(dbm.Task.status.in_(statuses))
        if schedule_name:
            stmt = stmt.filter(dbm.Schedule.name == schedule_name)

        # get total count of items matching the filters
        count = count_from_stmt(session, stmt)

        # get schedules from database
        return jsonify(
            {
                "meta": {"skip": skip, "limit": limit, "count": count},
                "items": list(
                    map(
                        TaskLightSchema().dump,
                        session.execute(stmt.offset(skip).limit(limit)).all(),
                    )
                ),
            }
        )


class TaskRoute(BaseRoute):
    rule = "/<string:task_id>"
    name = "task"
    methods = ["GET", "POST", "PATCH"]

    @auth_info_if_supplied
    @url_uuid("task_id")
    @dbsession
    def get(
        self, task_id: UUID, session: so.Session, token: AccessToken.Payload = None
    ):
        task = session.execute(
            sa.select(
                dbm.Task.id,
                dbm.Task.status,
                dbm.Task.timestamp,
                dbm.Task.config,
                dbm.Task.events,
                dbm.Task.debug,
                dbm.Task.requested_by,
                dbm.Task.canceled_by,
                dbm.Task.container,
                dbm.Task.priority,
                dbm.Task.notification,
                dbm.Task.files,
                dbm.Task.upload,
                dbm.Task.updated_at,
                dbm.Task.original_schedule_name,
                dbm.Schedule.name.label("schedule_name"),
                dbm.Worker.name.label("worker_name"),
            )
            .join(dbm.Worker, dbm.Task.worker, isouter=True)
            .join(dbm.Schedule, dbm.Task.schedule, isouter=True)
            .filter(dbm.Task.id == task_id)
        ).first()
        raise_if_none(task, TaskNotFound)

        task = TaskFullSchema().dump(task)

        request_args = request.args.to_dict()
        hide_secrets = "hide_secrets" in request_args

        # exclude notification to not expose private information (privacy)
        # on anonymous requests and requests for users without schedules_update
        if not token or not token.get_permission("schedules", "update"):
            task["notification"] = None

        if hide_secrets or not token or not token.get_permission("tasks", "create"):
            remove_secrets_from_response(task)

        return jsonify(task)

    @authenticate
    @require_perm("tasks", "create")
    @url_uuid("task_id")
    @dbsession
    def post(self, session: so.Session, task_id: UUID, token: AccessToken.Payload):
        """create a task from a requested_task_id"""

        if not ENABLED_SCHEDULER:
            raise make_response(
                jsonify({"msg": "scheduler is paused"}), HTTPStatus.NO_CONTENT
            )

        requested_task = dbm.RequestedTask.get(session, task_id, BadRequest)

        request_args = TaskCreateSchema().load(request.args.to_dict())
        worker_name = request_args["worker_name"]
        worker = dbm.Worker.get(session, worker_name, WorkerNotFound)
        task = dbm.Task(
            updated_at=requested_task.updated_at,
            events=requested_task.events,
            debug={},
            status=requested_task.status,
            timestamp=requested_task.timestamp,
            requested_by=requested_task.requested_by,
            canceled_by=None,
            container={},
            priority=requested_task.priority,
            config=requested_task.config,
            notification=requested_task.notification,
            files={},
            upload=requested_task.upload,
            original_schedule_name=requested_task.original_schedule_name,
        )
        task.id = requested_task.id
        task.schedule_id = requested_task.schedule_id
        task.worker_id = worker.id
        session.add(task)

        try:
            session.flush()
        except IntegrityError as exc:
            logger.exception(exc)
            response = jsonify({})
            response.status_code = HTTPStatus.LOCKED
            return response
        except Exception as exc:
            logger.exception(exc)
            raise exc

        task_id = task.id
        payload = {"worker": request_args["worker_name"]}
        try:
            task_event_handler(
                session=session,
                task_id=task_id,
                event=TaskStatus.reserved,
                payload=payload,
            )
        except Exception as exc:
            logger.exception(exc)
            logger.error("unable to create task. reverting.")
            raise exc

        session.delete(requested_task)

        return make_response(jsonify(TaskFullSchema().dump(task)), HTTPStatus.CREATED)

    @authenticate
    @require_perm("tasks", "update")
    @url_uuid("task_id")
    @dbsession
    def patch(self, session: so.Session, task_id: UUID, token: AccessToken.Payload):
        task = dbm.Task.get(session, task_id, TaskNotFound)

        try:
            request_json = TasKUpdateSchema().load(request.get_json())
            raise_if(not request.get_json(), ValidationError, "Update can't be empty")
        except ValidationError as e:
            raise InvalidRequestJSON(e.messages)

        task_event_handler(
            session=session,
            task_id=task.id,
            event=request_json["event"],
            payload=request_json["payload"],
        )

        return Response(status=HTTPStatus.NO_CONTENT)


class TaskCancelRoute(BaseRoute):
    rule = "/<string:task_id>/cancel"
    name = "task_cancel"
    methods = ["POST"]

    @authenticate
    @require_perm("tasks", "cancel")
    @url_uuid("task_id")
    @dbsession
    def post(self, session: so.Session, task_id: UUID, token: AccessToken.Payload):
        task = dbm.Task.get(session, task_id, TaskNotFound)
        if task.status not in TaskStatus.incomplete():
            raise TaskNotFound

        task_event_handler(
            session=session,
            task_id=task.id,
            event=TaskStatus.cancel_requested,
            payload={"canceled_by": token.username},
        )

        return Response(status=HTTPStatus.NO_CONTENT)
