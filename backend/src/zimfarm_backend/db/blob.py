from typing import cast
from uuid import UUID

from pydantic import AnyUrl
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.common.schemas.offliners.models import PreparedBlob
from zimfarm_backend.common.schemas.orms import BlobSchema
from zimfarm_backend.db.exceptions import RecordDoesNotExistError
from zimfarm_backend.db.models import Blob, Schedule


def get_blob_or_none(
    session: OrmSession, *, schedule_id: UUID, flag_name: str, checksum: str
) -> BlobSchema | None:
    """Get a blob using the unique combination of schedule_id, flag_name and checksum"""
    stmt = (
        select(Blob, Schedule.name.label("schedule_name"))
        .join(Schedule, Blob.schedule)
        .where(
            Blob.schedule_id == schedule_id,
            Blob.flag_name == flag_name,
            Blob.checksum == checksum,
        )
    )
    if row := session.execute(stmt).one_or_none():
        blob = cast(Blob, row.Blob)
        return BlobSchema(
            schedule_name=row.schedule_name,
            checksum=blob.checksum,
            url=AnyUrl(blob.url),
            flag_name=blob.flag_name,
            created_at=blob.created_at,
        )
    return None


def get_blob(
    session: OrmSession, *, schedule_id: UUID, flag_name: str, checksum: str
) -> BlobSchema:
    if blob := get_blob_or_none(
        session, schedule_id=schedule_id, flag_name=flag_name, checksum=checksum
    ):
        return blob
    raise RecordDoesNotExistError("Blob does not exist")


def create_or_update_blob(
    session: OrmSession,
    *,
    schedule_id: UUID,
    request: PreparedBlob,
):
    """Create or update a schedule blob"""
    values = request.model_dump(exclude_unset=True, mode="json", exclude={"data"})
    values["schedule_id"] = schedule_id
    stmt = insert(Blob).values(**values)
    stmt = stmt.on_conflict_do_update(
        index_elements=[Blob.schedule_id, Blob.flag_name, Blob.checksum],
        set_={
            **request.model_dump(
                exclude_unset=True,
                exclude={"flag_name", "checksum", "data"},
                mode="json",
            )
        },
    )
    session.execute(stmt)


def delete_blob(session: OrmSession, *, blob_id: UUID) -> int:
    """Delete a blob by its ID using the delete construct.

    Returns:
        The number of rows deleted (0 or 1)
    """
    stmt = delete(Blob).where(Blob.id == blob_id)
    result = session.execute(stmt)
    return result.rowcount
