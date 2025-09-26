from functools import partial

from zimfarm_backend.common.enums import Offliner
from zimfarm_backend.common.schemas import DashModel
from zimfarm_backend.common.schemas.offliners.builder import build_offliner_model

youtube_schema_creator = partial(
    build_offliner_model,
    model_name="YoutubeFlagsSchema",
    offliner_id=Offliner.youtube,
    base_model_cls=DashModel,
)
