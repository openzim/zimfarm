from functools import partial

from pydantic import field_validator

from zimfarm_backend.common.schemas import DashModel
from zimfarm_backend.common.schemas.fields import validate_comma_separated_zim_lang_code
from zimfarm_backend.common.schemas.offliners.builder import build_offliner_model

validators = {
    "customZimLanguage_validator": field_validator("customZimLanguage")(
        validate_comma_separated_zim_lang_code
    )
}

mwoffliner_schema_creator = partial(
    build_offliner_model,
    model_name="MWOfflinerFlagsSchema",
    offliner_id="mwoffliner",
    base_model_cls=DashModel,
    validators=validators,
)
