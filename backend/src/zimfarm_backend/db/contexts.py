from sqlalchemy import func, select, text, union
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.db import count_from_stmt
from zimfarm_backend.db.models import Schedule, Worker


class ContextListResult(BaseModel):
    nb_records: int
    contexts: list[str]


def get_contexts(session: OrmSession, skip: int, limit: int) -> ContextListResult:
    """Get a list of all unique contexts from schedules and workers"""
    # Get contexts from schedules (non-empty contexts)
    schedule_contexts = select(Schedule.context.label("context")).where(
        Schedule.context != ""
    )

    # Get contexts from workers (unnest the contexts array)
    worker_contexts = select(
        func.jsonb_object_keys(Worker.contexts).label("context")
    ).where(Worker.contexts != text("'{}'::jsonb"))

    # Union both queries to get all unique contexts.
    # UNION filters out duplicates in PostgreSQL.
    union_stmt = union(schedule_contexts, worker_contexts).order_by("context")

    return ContextListResult(
        nb_records=count_from_stmt(session, union_stmt),
        contexts=[
            context
            for (context,) in session.execute(
                union_stmt.offset(skip).limit(limit)
            ).all()
        ],
    )
