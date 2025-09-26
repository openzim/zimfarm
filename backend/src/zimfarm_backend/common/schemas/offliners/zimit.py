from functools import partial

from zimfarm_backend.common.enums import Offliner
from zimfarm_backend.common.schemas import CamelModel
from zimfarm_backend.common.schemas.offliners.builder import build_offliner_model

zimit_schema_creator = partial(
    build_offliner_model,
    model_name="ZimitFlagsSchema",
    offliner_id=Offliner.zimit,
    base_model_cls=CamelModel,
)
