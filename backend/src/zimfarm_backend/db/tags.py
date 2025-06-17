from sqlalchemy import func, select
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.db import count_from_stmt
from zimfarm_backend.db.models import Schedule


class TagListResult(BaseModel):
    nb_records: int
    tags: list[str]


def get_tags(session: OrmSession, skip: int, limit: int) -> TagListResult:
    """Get a list of schedule tags"""
    stmt = select(func.unnest(Schedule.tags).label("tag")).distinct().order_by("tag")
    return TagListResult(
        nb_records=count_from_stmt(session, stmt),
        tags=[tag for (tag,) in session.execute(stmt.offset(skip).limit(limit)).all()],
    )
