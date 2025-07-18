import pydantic
from pydantic import ConfigDict
from pydantic.alias_generators import to_camel


class BaseModel(pydantic.BaseModel):
    model_config = ConfigDict(
        use_enum_values=True, from_attributes=True, populate_by_name=True
    )


class CamelModel(pydantic.BaseModel):
    model_config = ConfigDict(
        use_enum_values=True,
        populate_by_name=True,
        from_attributes=True,
        alias_generator=to_camel,
    )


def to_kebab_case(string: str) -> str:
    return string.replace("_", "-")


class DashModel(pydantic.BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_kebab_case,
        use_enum_values=True,
    )
