from uuid import uuid4

import pytest
from pydantic import AnyUrl
from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.common.schemas.orms import CreateBlobSchema
from zimfarm_backend.db.blob import (
    create_or_update_blob,
    delete_blob,
    get_blob,
    get_blob_or_none,
    get_blobs,
)
from zimfarm_backend.db.exceptions import RecordDoesNotExistError
from zimfarm_backend.db.models import Blob, Recipe


def test_create_recipe_blob(dbsession: OrmSession, recipe: Recipe):
    create_or_update_blob(
        dbsession,
        recipe_id=recipe.id,
        request=CreateBlobSchema(
            kind="css",
            url=AnyUrl("https://www.example.com/style.css"),
            flag_name="custom-css",
            checksum="1",
        ),
    )
    dbsession.refresh(recipe)
    assert len(recipe.blobs) == 1


def test_update_recipe_blob(dbsession: OrmSession, recipe: Recipe):
    recipe.blobs.append(
        Blob(
            kind="css",
            flag_name="custom-css",
            url="https://www.example.com/style1.css",
            checksum="1",
        )
    )
    dbsession.add(recipe)
    dbsession.flush()

    create_or_update_blob(
        dbsession,
        recipe_id=recipe.id,
        request=CreateBlobSchema(
            kind="css",
            url=AnyUrl("https://www.example.com/style2.css"),
            flag_name="custom-css",
            checksum="1",
        ),
    )
    dbsession.refresh(recipe)
    assert len(recipe.blobs) == 1
    assert recipe.blobs[0].url == "https://www.example.com/style2.css"


def test_get_blob_or_none_found(dbsession: OrmSession, recipe: Recipe):
    recipe.blobs.append(
        Blob(
            kind="css",
            flag_name="custom-css",
            url="https://www.example.com/style.css",
            checksum="1",
        )
    )
    dbsession.add(recipe)
    dbsession.flush()

    blob = get_blob_or_none(
        dbsession,
        recipe_id=recipe.id,
        flag_name="custom-css",
        checksum="1",
    )
    assert blob is not None
    assert blob.flag_name == "custom-css"
    assert blob.checksum == "1"
    assert str(blob.url) == "https://www.example.com/style.css"


def test_get_blob_or_none_not_found(dbsession: OrmSession, recipe: Recipe):
    blob = get_blob_or_none(
        dbsession,
        recipe_id=recipe.id,
        flag_name="nonexistent",
        checksum="999",
    )
    assert blob is None


def test_get_blob_not_found(dbsession: OrmSession, recipe: Recipe):
    with pytest.raises(RecordDoesNotExistError):
        get_blob(
            dbsession,
            recipe_id=recipe.id,
            flag_name="nonexistent",
            checksum="999",
        )


def test_delete_blob_success(dbsession: OrmSession, recipe: Recipe):
    """Test successfully deleting a blob"""
    blob = Blob(
        kind="css",
        flag_name="custom-css",
        url="https://www.example.com/style.css",
        checksum="1",
    )
    recipe.blobs.append(blob)
    dbsession.add(recipe)
    dbsession.flush()

    blob_id = blob.id

    rows_deleted = delete_blob(dbsession, blob_id=blob_id)

    assert rows_deleted == 1

    # Verify blob is deleted from database
    result = dbsession.execute(select(Blob).where(Blob.id == blob_id)).first()
    assert result is None


def test_delete_blob_nonexistent(dbsession: OrmSession):
    """Test deleting a blob that doesn't exist"""

    nonexistent_id = uuid4()
    rows_deleted = delete_blob(dbsession, blob_id=nonexistent_id)

    assert rows_deleted == 0


@pytest.mark.parametrize(
    "skip,limit,expected_nb_records",
    [
        (0, 10, 10),
        (0, 5, 5),
        (10, 1, 0),
        (5, 10, 5),
    ],
)
def test_get_blobs(
    dbsession: OrmSession,
    recipe: Recipe,
    skip: int,
    limit: int,
    expected_nb_records: int,
):
    for i in range(10):
        recipe.blobs.append(
            Blob(
                kind="css",
                flag_name="custom-css",
                url=f"https://www.example.com/style{i}.css",
                checksum=f"{i}",
            )
        )
    dbsession.add(recipe)
    dbsession.flush()
    results = get_blobs(dbsession, skip=skip, limit=limit, recipe_name=recipe.name)
    assert len(results.blobs) == expected_nb_records
    assert len(results.blobs) <= limit


def test_get_blobs_wrong_recipe_name(
    dbsession: OrmSession,
    recipe: Recipe,
):
    recipe.blobs.append(
        Blob(
            kind="css",
            flag_name="custom-css",
            url="https://www.example.com/style.css",
            checksum="1",
        )
    )
    dbsession.add(recipe)
    dbsession.flush()
    results = get_blobs(dbsession, skip=0, limit=10, recipe_name=recipe.name + "wrong")
    assert len(results.blobs) == 0
