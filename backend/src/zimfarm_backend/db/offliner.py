from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from zimfarm_backend.common.schemas.models import DockerImageName
from zimfarm_backend.common.schemas.orms import OfflinerSchema
from zimfarm_backend.db.exceptions import (
    RecordAlreadyExistsError,
    RecordDoesNotExistError,
)
from zimfarm_backend.db.models import Offliner

# map to cache calls to get offliners since they should be immutable and are used a
# lot across the application
_cache_map: dict[str, OfflinerSchema] = {}


def create_offliner_schema(
    offliner: Offliner,
) -> OfflinerSchema:
    """Create an offliner from an offliner model"""
    return OfflinerSchema(
        id=offliner.id,
        base_model=offliner.base_model,
        docker_image_name=DockerImageName(offliner.docker_image_name),
        command_name=offliner.command_name,
    )


def create_offliner(
    session: Session,
    offliner_id: str,
    base_model: str,
    docker_image_name: str,
    command_name: str,
) -> OfflinerSchema:
    """Create an offliner in the database"""
    offliner = Offliner(
        id=offliner_id,
        base_model=base_model,
        docker_image_name=docker_image_name,
        command_name=command_name,
    )
    session.add(offliner)
    try:
        session.flush()
    except IntegrityError as exc:
        raise RecordAlreadyExistsError(f"Offliner '{offliner}' already exists") from exc
    return create_offliner_schema(offliner)


def get_offliner_by_id_or_none(
    session: Session, offliner_id: str
) -> OfflinerSchema | None:
    """Get an offliner model by id"""
    offliner = session.scalars(
        select(Offliner).where(Offliner.id == offliner_id)
    ).one_or_none()
    if offliner is not None:
        return create_offliner_schema(offliner)
    return None


def get_offliner(
    session: Session,
    offliner_id: str,
) -> OfflinerSchema:
    """Get an offliner model by id"""
    if offliner := _cache_map.get(offliner_id):
        return offliner

    if offliner := get_offliner_by_id_or_none(session, offliner_id):
        _cache_map[offliner_id] = offliner
        return offliner

    raise RecordDoesNotExistError(f"Offliner with id {offliner_id} does not exist")


def get_all_offliners(session: Session) -> list[OfflinerSchema]:
    """Get a list of all the available offliners."""
    offliners: list[OfflinerSchema] = []
    for offliner in session.scalars(select(Offliner)).all():
        offliner_schema = create_offliner_schema(offliner)
        _cache_map[offliner_schema.id] = offliner_schema
        offliners.append(offliner_schema)
    return offliners
