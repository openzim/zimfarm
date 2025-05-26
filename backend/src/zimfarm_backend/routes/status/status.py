import datetime
import logging

import sqlalchemy as sa
import sqlalchemy.orm as so
from flask import request

import db.models as dbm
from db import dbsession
from routes.base import BaseRoute
from routes.errors import BadRequest

logger = logging.getLogger(__name__)


class StatusMonitorRoute(BaseRoute):
    rule = "/<string:monitor_name>"
    name = "status"
    methods = ["GET"]

    def oldest_task_older_than(self, session: so.Session):
        request_args = request.args.to_dict()

        if not request_args.get("threshold_secs"):
            raise BadRequest("threshold_secs query parameter is mandatory")

        if not request_args.get("status"):
            raise BadRequest("status query parameter is mandatory")

        threshold_secs = int(request_args.get("threshold_secs"))
        status = request_args.get("status")

        now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        min_date: datetime.datetime = min(
            [now]
            + session.execute(
                (
                    sa.select(
                        dbm.Task.timestamp[status],
                    ).filter(dbm.Task.status == status)
                )
            )
            .scalars()
            .all(),
        )

        return (
            f"oldest_task_older_than for {status} and {threshold_secs}s: "
            f"{'KO' if (now-min_date).total_seconds() > threshold_secs else 'OK'}"
        )

    @dbsession
    def get(self, monitor_name: str, session: so.Session):
        """Get Zimfarm status for a given monitor"""

        handlers = {
            "oldest_task_older_than": self.oldest_task_older_than,
        }

        if monitor_name not in handlers:
            raise BadRequest(
                f"Monitor '{monitor_name}' is not supported. Supported "
                f"monitors: {','.join(handlers.keys())}"
            )

        return handlers[monitor_name](session)
