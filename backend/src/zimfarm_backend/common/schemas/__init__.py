import pydantic
from pydantic import ConfigDict
from pydantic.v1.utils import to_lower_camel


class BaseModel(pydantic.BaseModel):
    model_config = ConfigDict(use_enum_values=True, from_attributes=True)


class CamelModel(pydantic.BaseModel):
    model_config = ConfigDict(
        use_enum_values=True,
        from_attributes=True,
        alias_generator=to_lower_camel,
        extra="forbid",
    )


def to_kebab_case(string: str) -> str:
    return string.replace("_", "-")


class DashModel(pydantic.BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_kebab_case,
        use_enum_values=True,
        extra="forbid",
    )
