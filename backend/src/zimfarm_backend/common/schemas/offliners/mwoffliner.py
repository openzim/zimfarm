from functools import partial

from zimfarm_backend.common.enums import Offliner
from zimfarm_backend.common.schemas import DashModel
from zimfarm_backend.common.schemas.offliners.builder import build_offliner_model

mwoffliner_schema_creator = partial(
    build_offliner_model,
    model_name="MWOfflinerFlagsSchema",
    offliner_id=Offliner.mwoffliner,
    base_model_cls=DashModel,
)
