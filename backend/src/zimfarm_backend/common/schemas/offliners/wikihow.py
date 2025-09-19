from functools import partial

from zimfarm_backend.common.schemas import DashModel
from zimfarm_backend.common.schemas.offliners.builder import build_offliner_model

wikihow_schema_creator = partial(
    build_offliner_model,
    model_name="WikihowFlagsSchema",
    offliner_id="wikihow",
    base_model_cls=DashModel,
)
