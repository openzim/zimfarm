from functools import partial

from zimfarm_backend.common.enums import Offliner
from zimfarm_backend.common.schemas import DashModel
from zimfarm_backend.common.schemas.offliners.builder import build_offliner_model

openedx_schema_creator = partial(
    build_offliner_model,
    model_name="OpenedxFlagsSchema",
    offliner_id=Offliner.openedx,
    base_model_cls=DashModel,
)
