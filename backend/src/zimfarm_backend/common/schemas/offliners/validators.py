import re
from typing import Any

from pydantic import ValidationInfo


def validate_ted_links(value: str | None, info: ValidationInfo) -> str | None:
    if value is None:
        return value

    context = info.context
    if context and context.get("skip_validation"):
        return value

    for link in value.split(","):
        if not re.match(r"^https://www\.ted\.com/talks/[a-zA-Z0-9_-]+$", link):
            raise ValueError(f"Invalid TED talk URL: '{link}'")
    return value


def check_exclusive_fields(fields: list[str]):
    def _check_exclusive_fields(model: Any, info: ValidationInfo):
        context = info.context
        if context and context.get("skip_validation"):
            return model

        set_fields = [name for name in fields if getattr(model, name) is not None]

        if len(set_fields) != 1:
            raise ValueError(f"One and only one of fields in {fields} must be set")

        return model

    return _check_exclusive_fields
