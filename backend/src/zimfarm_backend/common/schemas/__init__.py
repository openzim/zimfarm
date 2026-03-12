import datetime
import warnings
from typing import Any

import pydantic
from pydantic import (
    ConfigDict,
    PrivateAttr,
    SerializerFunctionWrapHandler,
    model_serializer,
)
from pydantic.alias_generators import to_camel


def serialize_datetime(value: datetime.datetime) -> str:
    """Serialize datetime with 'Z' suffix for naive datetimes"""
    if value.tzinfo is None:
        return value.isoformat(timespec="seconds") + "Z"
    return value.isoformat(timespec="seconds")


class BaseModelWithOptionalValidation(pydantic.BaseModel):
    _constructed_without_validation: bool = PrivateAttr(default=False)

    @classmethod
    def build_model(cls, data: dict[str, Any], *, skip_validation: bool = False):
        if skip_validation:
            model = cls.model_construct(**data)
            model._constructed_without_validation = True
        else:
            model = cls.model_validate(
                data, context={"skip_validation": skip_validation}
            )
        return model

    @model_serializer(mode="wrap")
    def serialize_model(self, handler: SerializerFunctionWrapHandler):
        if self._constructed_without_validation:
            with warnings.catch_warnings():
                warnings.filterwarnings(
                    "ignore",
                    message=".*Pydantic serializer warnings.*",
                    category=UserWarning,
                )
                return handler(self)
        return handler(self)


class BaseModel(pydantic.BaseModel):
    model_config = ConfigDict(
        use_enum_values=True,
        from_attributes=True,
        populate_by_name=True,
        json_encoders={datetime.datetime: serialize_datetime},
        serialize_by_alias=True,
    )


class CamelModel(BaseModelWithOptionalValidation):
    model_config = ConfigDict(
        use_enum_values=True,
        populate_by_name=True,
        from_attributes=True,
        alias_generator=to_camel,
        json_encoders={datetime.datetime: serialize_datetime},
        serialize_by_alias=True,
    )


def to_kebab_case(string: str) -> str:
    return string.replace("_", "-")


class DashModel(BaseModelWithOptionalValidation):
    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_kebab_case,
        use_enum_values=True,
        json_encoders={datetime.datetime: serialize_datetime},
        serialize_by_alias=True,
    )
