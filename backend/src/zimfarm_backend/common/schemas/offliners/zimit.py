from functools import partial

from pydantic import field_validator

from zimfarm_backend.common.schemas import CamelModel
from zimfarm_backend.common.schemas.fields import validate_language_code
from zimfarm_backend.common.schemas.offliners.builder import build_offliner_model

validators = {"zim_lang_validator": field_validator("zim_lang")(validate_language_code)}

zimit_schema_creator = partial(
    build_offliner_model,
    model_name="ZimitFlagsSchema",
    offliner_id="zimit",
    base_model_cls=CamelModel,
    validators=validators,
)
