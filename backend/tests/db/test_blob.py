from pydantic import AnyUrl
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.common.schemas.offliners.models import ProcessedBlob
from zimfarm_backend.db.blob import create_or_update_blob
from zimfarm_backend.db.models import Blob, Schedule


def test_create_schedule_blob(dbsession: OrmSession, schedule: Schedule):
    create_or_update_blob(
        dbsession,
        schedule_id=schedule.id,
        request=ProcessedBlob(
            kind="css",
            url=AnyUrl("https://www.example.com/style.css"),
            flag_name="custom-css",
            checksum="1",
        ),
    )
    dbsession.refresh(schedule)
    assert len(schedule.blobs) == 1


def test_update_schedule_blob(dbsession: OrmSession, schedule: Schedule):
    schedule.blobs.append(
        Blob(
            kind="css",
            flag_name="custom-css",
            url="https://www.example.com/style1.css",
            checksum="1",
        )
    )
    dbsession.add(schedule)
    dbsession.flush()

    create_or_update_blob(
        dbsession,
        schedule_id=schedule.id,
        request=ProcessedBlob(
            kind="css",
            url=AnyUrl("https://www.example.com/style2.css"),
            flag_name="custom-css",
            checksum="1",
        ),
    )
    dbsession.refresh(schedule)
    assert len(schedule.blobs) == 1
    assert schedule.blobs[0].url == "https://www.example.com/style2.css"
