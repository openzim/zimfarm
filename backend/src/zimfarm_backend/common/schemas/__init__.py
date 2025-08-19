import datetime

import pydantic
from pydantic import ConfigDict
from pydantic.alias_generators import to_camel


def serialize_datetime(value: datetime.datetime) -> str:
    """Serialize datetime with 'Z' suffix for naive datetimes"""
    if value.tzinfo is None:
        return value.isoformat(timespec="seconds") + "Z"
    return value.isoformat(timespec="seconds")


class BaseModel(pydantic.BaseModel):
    model_config = ConfigDict(
        use_enum_values=True,
        from_attributes=True,
        populate_by_name=True,
        json_encoders={datetime.datetime: serialize_datetime},
    )


class CamelModel(pydantic.BaseModel):
    model_config = ConfigDict(
        use_enum_values=True,
        populate_by_name=True,
        from_attributes=True,
        alias_generator=to_camel,
        json_encoders={datetime.datetime: serialize_datetime},
    )


def to_kebab_case(string: str) -> str:
    return string.replace("_", "-")


class DashModel(pydantic.BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_kebab_case,
        use_enum_values=True,
        json_encoders={datetime.datetime: serialize_datetime},
    )
