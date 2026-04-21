from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.background_tasks.delete_orphaned_blobs import (
    delete_orphaned_blobs,
)
from zimfarm_backend.db import count_from_stmt
from zimfarm_backend.db.models import Blob, Recipe


def test_delete_orphaned_blobs_no_orphans(
    dbsession: OrmSession, recipe: Recipe, css_content: bytes
):
    """Test delete_orphaned_blobs when there are no orphaned blobs"""
    recipe.blobs.append(
        Blob(
            kind="css",
            flag_name="custom-css",
            checksum="1",
            url=None,
            content=css_content,
        )
    )
    recipe.blobs.append(
        Blob(
            kind="js",
            flag_name="custom-js",
            checksum="2",
            url=None,
            content=css_content,
        )
    )
    dbsession.add(recipe)
    dbsession.flush()

    delete_orphaned_blobs(dbsession)
    assert count_from_stmt(dbsession, select(Blob.id)) == 2


def test_delete_orphaned_blobs_deletes_orphans(
    dbsession: OrmSession, recipe: Recipe, css_content: bytes
):
    """Test delete_orphaned_blobs successfully deletes orphaned blobs"""
    orphaned_blob1 = Blob(
        kind="css",
        flag_name="custom-css",
        checksum="1",
        url=None,
        content=css_content,
    )
    orphaned_blob2 = Blob(
        kind="js",
        flag_name="custom-js",
        checksum="2",
        url=None,
        content=css_content,
    )
    dbsession.add_all([orphaned_blob1, orphaned_blob2])
    dbsession.flush()

    # Create a non-orphaned blob
    recipe.blobs.append(
        Blob(
            kind="css",
            flag_name="active-css",
            checksum="3",
            url=None,
            content=css_content,
        )
    )
    dbsession.add(recipe)
    dbsession.flush()

    delete_orphaned_blobs(dbsession)
    assert count_from_stmt(dbsession, select(Blob.recipe_id)) == 1
