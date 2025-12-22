from typing import cast
from uuid import UUID

from pydantic import AnyUrl
from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.common.schemas.orms import BlobSchema, CreateBlobSchema
from zimfarm_backend.db.exceptions import RecordDoesNotExistError
from zimfarm_backend.db.models import Blob, Schedule


class BlobListResult(BaseModel):
    nb_records: int
    blobs: list[BlobSchema]


def get_blobs(
    session: OrmSession,
    *,
    schedule_name: str,
    skip: int,
    limit: int,
) -> BlobListResult:
    """Get a list of blobs for the schedule"""
    query = (
        select(
            func.count().over().label("nb_records"),
            Blob,
        )
        .where(
            Schedule.name == schedule_name,
        )
        .offset(skip)
        .limit(limit)
        .order_by(Blob.created_at.desc())
    )

    results = BlobListResult(nb_records=0, blobs=[])
    for nb_records, blob in session.execute(query).all():
        blob = cast(Blob, blob)
        results.nb_records = nb_records
        results.blobs.append(_create_blob_schema(blob))
    return results


def _create_blob_schema(blob: Blob) -> BlobSchema:
    return BlobSchema(
        id=blob.id,
        checksum=blob.checksum,
        url=AnyUrl(blob.url),
        kind=blob.kind,
        flag_name=blob.flag_name,
        created_at=blob.created_at,
        schedule_id=blob.schedule_id,
        comments=blob.comments,
    )


def get_blob_by_id_or_none(session: OrmSession, *, blob_id: UUID) -> BlobSchema | None:
    """Get a blob by its ID"""
    stmt = select(Blob).join(Schedule, Blob.schedule).where(Blob.id == blob_id)
    blob = session.scalars(stmt).one_or_none()
    if blob:
        return _create_blob_schema(blob)
    return None


def get_blob_by_id(session: OrmSession, *, blob_id: UUID) -> BlobSchema:
    if blob := get_blob_by_id_or_none(session, blob_id=blob_id):
        return blob
    raise RecordDoesNotExistError("Blob does not exist")


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
    blob = session.scalars(stmt).one_or_none()
    if blob:
        return _create_blob_schema(blob)
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
    request: CreateBlobSchema,
):
    """Create or update a schedule blob"""
    values = request.model_dump(
        exclude_unset=True,
        mode="json",
    )
    values["schedule_id"] = schedule_id
    stmt = insert(Blob).values(**values)
    stmt = stmt.on_conflict_do_update(
        index_elements=[Blob.schedule_id, Blob.flag_name, Blob.checksum],
        set_={
            **request.model_dump(
                exclude_unset=True,
                exclude={"flag_name", "checksum"},
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
