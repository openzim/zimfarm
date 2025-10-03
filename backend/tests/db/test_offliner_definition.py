from contextlib import nullcontext as does_not_raise
from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.common import getnow
from zimfarm_backend.common.enums import DockerImageName
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
    update_offliner_definition,
    update_offliner_flags,
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


def test_update_offliner_definition(
    dbsession: OrmSession,
    mwoffliner_flags: OfflinerSpecSchema,
    mwoffliner_definition: OfflinerDefinitionSchema,
    mwoffliner: OfflinerSchema,
):
    with does_not_raise():
        update_offliner_definition(
            dbsession, mwoffliner.id, mwoffliner_definition.version, mwoffliner_flags
        )


def test_update_offliner_definition_error(
    dbsession: OrmSession,
    mwoffliner_flags: OfflinerSpecSchema,
    mwoffliner_definition: OfflinerDefinitionSchema,
):
    with pytest.raises(RecordDoesNotExistError):
        update_offliner_definition(
            dbsession, "ted", mwoffliner_definition.version, mwoffliner_flags
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


@pytest.mark.parametrize(
    "new_spec, data, name_mappings, expected_data",
    [
        pytest.param(
            """{
            "offliner_id": "mwoffliner",
            "stdOutput": false,
            "stdStats": false,
            "flags": {
                "mwUrl": {
                "type": "url",
                "required": true,
                "title": "Wiki URL",
                "description": "The URL of the mediawiki to scrape"
                },
                "adminEmail": {
                "type": "email",
                "required": true,
                "title": "Admin Email",
                "description": "Email"
                },
                "articleList": {
                "type": "string",
                "required": false,
                "title": "Article List",
                "description": "List of articles to include"
                },
                "articleListToIgnore": {
                "type": "string",
                "required": false,
                "title": "Article List to ignore",
                "description": "List of articles to ignore"
                }
            }
        }""",
            {
                "offliner_id": "mwoffliner",
                "mwUrl": "https://en.wikipedia.org/",
                "adminEmail": "test@example.com",
                "articleList": "Article1,Article2",
            },
            {"+": "articleListToIgnore"},
            {
                "offliner_id": "mwoffliner",
                "mwUrl": "https://en.wikipedia.org/",
                "adminEmail": "test@example.com",
                "articleList": "Article1,Article2",
                "articleListToIgnore": None,
            },
            id="add-new-field-with-default-none",
        ),
        pytest.param(
            """{
            "offliner_id": "mwoffliner",
            "stdOutput": false,
            "stdStats": false,
            "flags": {
                "adminEmail": {
                "type": "email",
                "required": true,
                "title": "Admin Email",
                "description": "Email"
                },
                "articleList": {
                "type": "string",
                "required": false,
                "title": "Article List",
                "description": "List of articles to include"
                }
            }
        }""",
            {
                "offliner_id": "mwoffliner",
                "mwUrl": "https://en.wikipedia.org/",
                "adminEmail": "test@example.com",
                "articleList": "Article1,Article2",
            },
            {"mwUrl": "-"},
            {
                "offliner_id": "mwoffliner",
                "adminEmail": "test@example.com",
                "articleList": "Article1,Article2",
            },
            id="remove-field",
        ),
        pytest.param(
            """{
            "offliner_id": "mwoffliner",
            "stdOutput": false,
            "stdStats": false,
            "flags": {
                "mwUrl": {
                "type": "url",
                "required": true,
                "title": "Wiki URL",
                "description": "The URL of the mediawiki to scrape"
                },
                "Email": {
                "type": "email",
                "required": true,
                "title": "Admin Email",
                "description": "Email"
                },
                "articleList": {
                "type": "string",
                "required": false,
                "title": "Article List",
                "description": "List of articles to include"
                }
            }
        }""",
            {
                "offliner_id": "mwoffliner",
                "mwUrl": "https://en.wikipedia.org/",
                "adminEmail": "test@example.com",
                "articleList": "Article1,Article2",
            },
            {"adminEmail": "Email"},
            {
                "offliner_id": "mwoffliner",
                "mwUrl": "https://en.wikipedia.org/",
                "email": "test@example.com",
                "articleList": "Article1,Article2",
            },
            id="rename-field",
        ),
    ],
)
def test_update_offliner_flags(
    new_spec: str,
    data: dict[str, Any],
    name_mappings: dict[str, str],
    expected_data: dict[str, Any],
):
    # This is the old spec that we are updating
    OfflinerSpecSchema.model_validate_json(
        """{
            "offliner_id": "mwoffliner",
            "stdOutput": false,
            "stdStats": false,
            "flags": {
                "mwUrl": {
                "type": "url",
                "required": true,
                "title": "Wiki URL",
                "description": "The URL of the mediawiki to scrape"
                },
                "adminEmail": {
                "type": "email",
                "required": true,
                "title": "Admin Email",
                "description": "Email"
                },
                "articleList": {
                "type": "string",
                "required": false,
                "title": "Article List",
                "description": "List of articles to include"
                }
            }
        }"""
    )

    schema = OfflinerSpecSchema.model_validate_json(new_spec)
    offliner = OfflinerSchema(
        id="mwoffliner",
        base_model="CamelModel",
        docker_image_name=DockerImageName.mwoffliner,
        command_name="mwoffliner",
        ci_secret_hash=None,
    )
    new_definition = OfflinerDefinitionSchema(
        id=uuid4(),
        offliner=offliner.id,
        version="initial",
        schema_=schema,
        created_at=getnow(),
    )
    updated_data = update_offliner_flags(
        offliner=offliner,
        offliner_definition=new_definition,
        data=data,
        name_mappings=name_mappings,
    )
    assert updated_data == expected_data
