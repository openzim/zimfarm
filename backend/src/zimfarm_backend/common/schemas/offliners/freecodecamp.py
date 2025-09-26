from functools import partial

from zimfarm_backend.common.enums import Offliner
from zimfarm_backend.common.schemas import DashModel
from zimfarm_backend.common.schemas.offliners.builder import build_offliner_model

freecodecamp_schema_creator = partial(
    build_offliner_model,
    model_name="FreeCodeCampFlagsSchema",
    offliner_id=Offliner.freecodecamp,
    base_model_cls=DashModel,
)
