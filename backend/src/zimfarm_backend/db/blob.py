from uuid import UUID

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.common.schemas.offliners.models import ProcessedBlob
from zimfarm_backend.db.models import Blob


def create_or_update_blob(
    session: OrmSession,
    *,
    schedule_id: UUID,
    request: ProcessedBlob,
):
    """Create or update a schedule blob"""
    values = request.model_dump(exclude_unset=True, mode="json")
    values["schedule_id"] = schedule_id
    stmt = insert(Blob).values(**values)
    stmt = stmt.on_conflict_do_update(
        index_elements=[Blob.schedule_id, Blob.flag_name, Blob.checksum],
        set_={
            **request.model_dump(
                exclude_unset=True, exclude={"flag_name", "checksum"}, mode="json"
            )
        },
    )
    session.execute(stmt)
