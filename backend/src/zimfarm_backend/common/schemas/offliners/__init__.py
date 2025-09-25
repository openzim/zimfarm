from pydantic import BaseModel

from zimfarm_backend.common.constants import (
    NAUTILUS_USE_RELAXED_SCHEMA,
    ZIMIT_USE_RELAXED_SCHEMA,
)
from zimfarm_backend.common.enums import Offliner
from zimfarm_backend.common.schemas.offliners.builder import OfflinerSchema
from zimfarm_backend.common.schemas.offliners.devdocs import devdocs_schema_creator
from zimfarm_backend.common.schemas.offliners.freecodecamp import (
    freecodecamp_schema_creator,
)
from zimfarm_backend.common.schemas.offliners.gutenberg import gutenberg_schema_creator
from zimfarm_backend.common.schemas.offliners.ifixit import ifixit_schema_creator
from zimfarm_backend.common.schemas.offliners.kolibri import kolibri_schema_creator
from zimfarm_backend.common.schemas.offliners.mindtouch import mindtouch_schema_creator
from zimfarm_backend.common.schemas.offliners.mwoffliner import (
    mwoffliner_schema_creator,
)
from zimfarm_backend.common.schemas.offliners.nautilus import nautilus_schema_creator
from zimfarm_backend.common.schemas.offliners.openedx import openedx_schema_creator
from zimfarm_backend.common.schemas.offliners.phet import phet_schema_creator
from zimfarm_backend.common.schemas.offliners.sotoki import sotoki_schema_creator
from zimfarm_backend.common.schemas.offliners.ted import ted_schema_creator
from zimfarm_backend.common.schemas.offliners.wikihow import wikihow_schema_creator
from zimfarm_backend.common.schemas.offliners.youtube import youtube_schema_creator
from zimfarm_backend.common.schemas.offliners.zimit import zimit_schema_creator

_registry = {
    Offliner.mwoffliner: mwoffliner_schema_creator,
    Offliner.youtube: youtube_schema_creator,
    Offliner.gutenberg: gutenberg_schema_creator,
    Offliner.phet: phet_schema_creator,
    Offliner.sotoki: sotoki_schema_creator,
    Offliner.nautilus: nautilus_schema_creator,
    Offliner.openedx: openedx_schema_creator,
    Offliner.ted: ted_schema_creator,
    Offliner.wikihow: wikihow_schema_creator,
    Offliner.zimit: zimit_schema_creator,
    Offliner.kolibri: kolibri_schema_creator,
    Offliner.devdocs: devdocs_schema_creator,
    Offliner.mindtouch: mindtouch_schema_creator,
    Offliner.freecodecamp: freecodecamp_schema_creator,
    Offliner.ifixit: ifixit_schema_creator,
}

_slug_regex = "^[A-Za-z0-9._-]+$"


def create_offliner_schema(
    offliner: Offliner, schema: OfflinerSchema
) -> type[BaseModel]:
    match offliner:
        case Offliner.nautilus:
            if NAUTILUS_USE_RELAXED_SCHEMA:
                schema.flags["zim_file"].pattern = _slug_regex
            return nautilus_schema_creator(schema=schema)
        case Offliner.zimit:
            if ZIMIT_USE_RELAXED_SCHEMA:
                schema.flags["zim_file"].pattern = _slug_regex
                schema.flags["name"].pattern = _slug_regex
            return zimit_schema_creator(schema=schema)
        case _:
            return _registry[offliner](schema=schema)
