from uuid import UUID

from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.common.schemas.offliners.models import ProcessedBlob
from zimfarm_backend.db.models import Blob


def create_blob(
    session: OrmSession,
    *,
    schedule_id: UUID,
    request: ProcessedBlob,
) -> Blob:
    """Create a schedule blob"""
    blob = Blob(kind=request.kind, url=str(request.url), flag_name=request.flag_name)
    blob.schedule_id = schedule_id
    session.add(blob)
    session.flush()
    return blob
