from functools import partial

from zimfarm_backend.common.schemas import DashModel
from zimfarm_backend.common.schemas.offliners.builder import (
    build_offliner_model,
)

ifixit_schema_creator = partial(
    build_offliner_model,
    model_name="IFixitFlagsSchema",
    offliner_id="ifixit",
    base_model_cls=DashModel,
)
