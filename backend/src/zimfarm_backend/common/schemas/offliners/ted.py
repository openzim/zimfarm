import re
from functools import partial
from typing import Any

from pydantic import ValidationInfo, field_validator, model_validator

from zimfarm_backend.common.schemas import DashModel
from zimfarm_backend.common.schemas.fields import validate_comma_separated_zim_lang_code
from zimfarm_backend.common.schemas.offliners.builder import build_offliner_model


def validate_links(value: str | None, info: ValidationInfo) -> str | None:
    if value is None:
        return value

    context = info.context
    if context and context.get("skip_validation"):
        return value

    for link in value.split(","):
        if not re.match(r"^https://www\.ted\.com/talks/[a-zA-Z0-9_-]+$", link):
            raise ValueError(f"Invalid TED talk URL: '{link}'")
    return value


def check_exclusive_fields(self: Any, info: ValidationInfo) -> Any:
    context = info.context
    if context and context.get("skip_validation"):
        return self

    set_fields = [
        name
        for name in ("links", "topics", "playlists")
        if getattr(self, name) is not None
    ]

    if len(set_fields) != 1:
        raise ValueError(
            "One and only one of 'links', 'topics', or 'playlists' must be set"
        )

    return self


validators = {
    "languages_validator": field_validator("languages")(
        validate_comma_separated_zim_lang_code
    ),
    "links_validator": field_validator("links")(validate_links),
    "check_exclusive_fields_validator": model_validator(mode="after")(
        check_exclusive_fields
    ),
}

ted_schema_creator = partial(
    build_offliner_model,
    model_name="TedFlagsSchema",
    offliner_id="ted",
    base_model_cls=DashModel,
    validators=validators,  # pyright: ignore[reportArgumentType]
)
