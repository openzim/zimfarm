from pydantic import AnyUrl
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.common.schemas.offliners.models import ProcessedBlob
from zimfarm_backend.db.blob import create_blob
from zimfarm_backend.db.models import Schedule


def test_create_schedule_blob(dbsession: OrmSession, schedule: Schedule):
    create_blob(
        dbsession,
        schedule_id=schedule.id,
        request=ProcessedBlob(
            kind="css",
            url=AnyUrl("https://www.example.com/style.css"),
            flag_name="custom-css",
        ),
    )
    dbsession.refresh(schedule)
    assert len(schedule.blobs) == 1
