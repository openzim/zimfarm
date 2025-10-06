from copy import deepcopy
from typing import Any
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from zimfarm_backend import logger
from zimfarm_backend.common import getnow
from zimfarm_backend.common.schemas.offliners.builder import build_offliner_model
from zimfarm_backend.common.schemas.offliners.models import OfflinerSpecSchema
from zimfarm_backend.common.schemas.orms import OfflinerDefinitionSchema, OfflinerSchema
from zimfarm_backend.db.exceptions import RecordDoesNotExistError
from zimfarm_backend.db.models import OfflinerDefinition


class OfflinerVersionsListResult(BaseModel):
    """Result of query to list offliner versions from the database."""

    nb_records: int
    versions: list[str]


def create_offliner_definition_schema(
    offliner_definition: OfflinerDefinition,
) -> OfflinerDefinitionSchema:
    """Create the offliner definition schema"""
    return OfflinerDefinitionSchema(
        id=offliner_definition.id,
        offliner=offliner_definition.offliner,
        version=offliner_definition.version,
        created_at=offliner_definition.created_at,
        schema_=OfflinerSpecSchema.model_validate(offliner_definition.schema),
    )


def create_offliner_definition(
    session: Session,
    schema: OfflinerSpecSchema,
    offliner: str,
    version: str,
) -> OfflinerDefinitionSchema:
    """Create an offliner definition in the database"""
    insert_stmt = insert(OfflinerDefinition).values(
        schema=schema.model_dump(mode="json"),
        version=version,
        created_at=getnow(),
        offliner=offliner,
    )
    insert_stmt = insert_stmt.on_conflict_do_update(
        index_elements=[OfflinerDefinition.offliner, OfflinerDefinition.version],
        set_={
            OfflinerDefinition.schema: schema.model_dump(mode="json"),
        },
    )
    session.execute(insert_stmt)
    return get_offliner_definition(session, offliner, version)


def create_offliner_instance(
    *,
    offliner: OfflinerSchema,
    offliner_definition: OfflinerDefinitionSchema | OfflinerDefinition,
    data: dict[str, Any],
    skip_validation: bool = True,
) -> BaseModel:
    """Create the offliner instance from the offliner definition and data"""
    if isinstance(offliner_definition, OfflinerDefinition):
        offliner_definition = create_offliner_definition_schema(offliner_definition)
    return build_offliner_model(
        offliner,
        offliner_definition.schema_,
    ).model_validate(data, context={"skip_validation": skip_validation})


def get_offliner_definition_or_none(
    session: Session,
    offliner_id: str,
    version: str,
) -> OfflinerDefinitionSchema | None:
    """Get the offliner definition or None using the offliner and version"""
    definition = session.scalars(
        select(OfflinerDefinition).where(
            OfflinerDefinition.offliner == offliner_id,
            OfflinerDefinition.version == version,
        )
    ).one_or_none()
    if definition is not None:
        return create_offliner_definition_schema(definition)


def get_offliner_definition(
    session: Session,
    offliner_id: str,
    version: str,
) -> OfflinerDefinitionSchema:
    """Get the offliner definition using the offliner and version"""
    if (
        offliner_definition := get_offliner_definition_or_none(
            session, offliner_id, version
        )
    ) is None:
        raise RecordDoesNotExistError(
            f"Offliner definition for offliner {offliner_id} with version "
            f"{version} does not exist"
        )
    return offliner_definition


def get_offliner_definition_by_id_or_none(
    session: Session,
    offliner_definition_id: UUID,
) -> OfflinerDefinitionSchema | None:
    """Get the offliner definition or None using the offliner definition id"""
    definition = session.scalars(
        select(OfflinerDefinition).where(
            OfflinerDefinition.id == offliner_definition_id
        )
    ).one_or_none()
    if definition is not None:
        return create_offliner_definition_schema(definition)
    return None


def get_offliner_definition_by_id(
    session: Session,
    offliner_definition_id: UUID,
) -> OfflinerDefinitionSchema:
    """Get the offliner definition using the offliner definition id"""
    if (
        offliner_definition := get_offliner_definition_by_id_or_none(
            session, offliner_definition_id
        )
    ) is None:
        raise RecordDoesNotExistError(
            f"Offliner definition with id {offliner_definition_id} does not exist"
        )
    return offliner_definition


def get_offliner_versions(
    session: Session,
    offliner_id: str,
    *,
    skip: int,
    limit: int,
) -> OfflinerVersionsListResult:
    """Get the versions of the offliner"""
    results = OfflinerVersionsListResult(nb_records=0, versions=[])
    stmt = (
        select(func.count().over().label("nb_records"), OfflinerDefinition.version)
        .where(OfflinerDefinition.offliner == offliner_id)
        .order_by(OfflinerDefinition.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    for nb_records, version in session.execute(stmt).all():
        results.nb_records = nb_records
        results.versions.append(version)
    return results


def update_offliner_flags(
    *,
    offliner: OfflinerSchema,
    offliner_definition: OfflinerDefinitionSchema,
    data: dict[str, Any],
    name_mappings: dict[str, str],
) -> dict[str, Any]:
    """Generate new data to conform to the new offliner definition flags.

    name_mappings specifies a dictionary of names in the old spec to the
    names in the new spec.

    Validation errors will be raised if the data does not conform to the new spec.
    """
    new_data = deepcopy(data)

    # The cases for the updates are:
    # - Remove the field with name from data
    # - Add a new field to data with default of None
    # - Update the field with name to the new name

    for old_name, new_name in name_mappings.items():
        if old_name == "+":
            # Add the new name to the data with a default of None
            new_data[new_name] = None
            continue

        if old_name not in data:
            # Sometimes, the old name does not exist in the DB probably because
            # it was a nullable field and got validated regardless
            logger.warning(f"Key '{old_name}' not found in data. Skipping...")
            continue

        if new_name == "-":
            del new_data[old_name]
        elif new_name != old_name:
            new_data[new_name] = data[old_name]
            del new_data[old_name]

    # validate the new data and return it
    return create_offliner_instance(
        offliner=offliner,
        offliner_definition=offliner_definition,
        data=new_data,
        skip_validation=True,
    ).model_dump(mode="json")


def update_offliner_definition(
    session: Session,
    offliner_id: str,
    version: str,
    spec: OfflinerSpecSchema,
) -> OfflinerDefinitionSchema:
    """Update the offliner definition using the offliner and version"""
    stmt = (
        update(OfflinerDefinition)
        .where(
            OfflinerDefinition.offliner == offliner_id,
            OfflinerDefinition.version == version,
        )
        .values(schema=spec.model_dump(mode="json"))
    )
    result = session.execute(stmt)
    if result.rowcount == 0:
        raise RecordDoesNotExistError(
            f"Offliner definition for offliner {offliner_id} with version "
            f"{version} does not exist"
        )
    return get_offliner_definition(session, offliner_id, version)
