from functools import partial

from pydantic import field_validator

from zimfarm_backend.common.schemas import DashModel
from zimfarm_backend.common.schemas.fields import validate_language_code
from zimfarm_backend.common.schemas.offliners.builder import build_offliner_model

validators = {"lang_validator": field_validator("lang")(validate_language_code)}

kolibri_schema_creator = partial(
    build_offliner_model,
    model_name="KolibriFlagsSchema",
    offliner_id="kolibri",
    base_model_cls=DashModel,
    validators=validators,
)
