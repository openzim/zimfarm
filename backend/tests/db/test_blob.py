import pytest
from pydantic import AnyUrl
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.common.schemas.offliners.models import PreparedBlob
from zimfarm_backend.db.blob import create_or_update_blob, get_blob, get_blob_or_none
from zimfarm_backend.db.exceptions import RecordDoesNotExistError
from zimfarm_backend.db.models import Blob, Schedule


def test_create_schedule_blob(dbsession: OrmSession, schedule: Schedule):
    create_or_update_blob(
        dbsession,
        schedule_id=schedule.id,
        request=PreparedBlob(
            kind="css",
            url=AnyUrl("https://www.example.com/style.css"),
            flag_name="custom-css",
            checksum="1",
            data=b"hello",
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
        request=PreparedBlob(
            kind="css",
            url=AnyUrl("https://www.example.com/style2.css"),
            flag_name="custom-css",
            checksum="1",
            data=b"hello",
        ),
    )
    dbsession.refresh(schedule)
    assert len(schedule.blobs) == 1
    assert schedule.blobs[0].url == "https://www.example.com/style2.css"


def test_get_blob_or_none_found(dbsession: OrmSession, schedule: Schedule):
    schedule.blobs.append(
        Blob(
            kind="css",
            flag_name="custom-css",
            url="https://www.example.com/style.css",
            checksum="1",
        )
    )
    dbsession.add(schedule)
    dbsession.flush()

    blob = get_blob_or_none(
        dbsession,
        schedule_id=schedule.id,
        flag_name="custom-css",
        checksum="1",
    )
    assert blob is not None
    assert blob.flag_name == "custom-css"
    assert blob.checksum == "1"
    assert str(blob.url) == "https://www.example.com/style.css"
    assert blob.schedule_name == schedule.name


def test_get_blob_or_none_not_found(dbsession: OrmSession, schedule: Schedule):
    blob = get_blob_or_none(
        dbsession,
        schedule_id=schedule.id,
        flag_name="nonexistent",
        checksum="999",
    )
    assert blob is None


def test_get_blob_not_found(dbsession: OrmSession, schedule: Schedule):
    with pytest.raises(RecordDoesNotExistError):
        get_blob(
            dbsession,
            schedule_id=schedule.id,
            flag_name="nonexistent",
            checksum="999",
        )
