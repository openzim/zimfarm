from contextlib import nullcontext as does_not_raise
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.common.schemas.offliners.models import OfflinerSpecSchema
from zimfarm_backend.common.schemas.orms import OfflinerDefinitionSchema, OfflinerSchema
from zimfarm_backend.db.exceptions import (
    RecordAlreadyExistsError,
    RecordDoesNotExistError,
)
from zimfarm_backend.db.offliner_definition import (
    create_offliner_definition,
    get_offliner_definition,
    get_offliner_definition_by_id,
    get_offliner_versions,
)


def test_get_offliner_definition_missing(
    dbsession: OrmSession, ted_offliner: OfflinerSchema
):
    with pytest.raises(RecordDoesNotExistError):
        get_offliner_definition(dbsession, ted_offliner.id, "initial")


def test_get_offliner_definition_exists(
    dbsession: OrmSession,
    tedoffliner_definition: OfflinerDefinitionSchema,
    ted_offliner: OfflinerSchema,
):
    offliner_definition = get_offliner_definition(
        dbsession, ted_offliner.id, tedoffliner_definition.version
    )
    assert offliner_definition.id == tedoffliner_definition.id


def test_get_offliner_definition_by_id_missing(dbsession: OrmSession):
    with pytest.raises(RecordDoesNotExistError):
        get_offliner_definition_by_id(dbsession, uuid4())


def test_get_offliner_definition_by_id_exists(
    dbsession: OrmSession, tedoffliner_definition: OfflinerDefinitionSchema
):
    offliner_definition = get_offliner_definition_by_id(
        dbsession, tedoffliner_definition.id
    )
    assert offliner_definition.id == tedoffliner_definition.id


def test_create_offliner_definition(
    dbsession: OrmSession,
    mwoffliner_flags: OfflinerSpecSchema,
    mwoffliner: OfflinerSchema,
):
    with does_not_raise():
        create_offliner_definition(
            dbsession, mwoffliner_flags, mwoffliner.id, version="initial"
        )


def test_create_offliner_definition_with_duplicate_version(
    dbsession: OrmSession,
    mwoffliner_flags: OfflinerSpecSchema,
    mwoffliner_definition: OfflinerDefinitionSchema,  # noqa: ARG001 (needed for side effect)
    mwoffliner: OfflinerSchema,
):
    with pytest.raises(RecordAlreadyExistsError):
        create_offliner_definition(
            dbsession, mwoffliner_flags, mwoffliner.id, version="initial"
        )


def test_create_offliner_definition_with_different_version(
    dbsession: OrmSession,
    mwoffliner_flags: OfflinerSpecSchema,
    mwoffliner_definition: OfflinerDefinitionSchema,  # noqa: ARG001 (needed for side effect)
    mwoffliner: OfflinerSchema,
):
    with does_not_raise():
        create_offliner_definition(
            dbsession, mwoffliner_flags, mwoffliner.id, version="v2"
        )


@pytest.mark.parametrize(
    "offliner_id, limit, skip, expected_nb_records, expected_versions",
    [
        pytest.param("ted", 10, 0, 1, ["initial"], id="ted"),
        pytest.param("ted", 10, 1, 0, [], id="ted_skip_1"),
        pytest.param("mwoffliner", 10, 0, 1, ["initial"], id="mwoffliner"),
        pytest.param("mwoffliner", 10, 1, 0, [], id="mwoffliner_skip_1"),
    ],
)
def test_get_offliner_versions(
    dbsession: OrmSession,
    ted_offliner: OfflinerSchema,  # noqa: ARG001 needed for side effect
    tedoffliner_definition: OfflinerDefinitionSchema,  # noqa: ARG001 needed for side effect
    mwoffliner: OfflinerSchema,  # noqa: ARG001 needed for side effect
    mwoffliner_definition: OfflinerDefinitionSchema,  # noqa: ARG001 needed for side effect
    offliner_id: str,
    limit: int,
    skip: int,
    expected_nb_records: int,
    expected_versions: list[str],
):
    results = get_offliner_versions(dbsession, offliner_id, skip=skip, limit=limit)
    assert results.nb_records == expected_nb_records
    assert results.versions == expected_versions
