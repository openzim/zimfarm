# ruff: noqa: UP007
from collections.abc import Callable
from enum import Enum, StrEnum
from typing import Annotated, Any, Literal, Optional, cast

from pydantic import (
    EmailStr,
    Field,
    ValidationInfo,
    WrapValidator,
    create_model,
)

from zimfarm_backend.common.schemas import BaseModel, CamelModel, DashModel
from zimfarm_backend.common.schemas.fields import (
    NotEmptyString,
    OptionalField,
    SecretUrl,
    SkipableBool,
    SkipableUrl,
    ZIMSecretStr,
    enum_member,
    skip_validation,
)
from zimfarm_backend.common.schemas.offliners.models import (
    BaseFlagSchema,
    Choice,
)


class FlagSchema(BaseFlagSchema):
    type: Literal[
        "string",
        "boolean",
        "float",
        "integer",
        "url",
        "email",
        "string-enum",
        "list-of-integer",
        "list-of-string",
        "list-of-boolean",
        "list-of-string-enum",
        "list-of-url",
        "list-of-email",
    ]
    choices: list[str] | list[Choice] | None = None
    alias: str | None = None


class OfflinerSchema(CamelModel):
    flags: dict[str, FlagSchema]


# These are simple types that don't need any special handling
TYPE_MAP = {
    "boolean": SkipableBool,
    "integer": int,
    "float": float,
    "email": EmailStr,
    "list-of-boolean": list[SkipableBool],
    "list-of-integer": list[int],
    "list-of-float": list[float],
    "list-of-email": list[EmailStr],
}


def generate_field_type(flag: FlagSchema, label: str):
    """Generate the type for a flag with necessary metadata in annotations"""
    # Build up the pydantic field with necessary metadata
    pydantic_field_cls = Field if flag.required else OptionalField
    pydantic_field = pydantic_field_cls(
        title=flag.title,
        description=flag.description,
        ge=flag.min,
        le=flag.max,
        pattern=flag.pattern,
        min_length=flag.min_length,
        max_length=flag.max_length,
        alias=flag.alias,
    )
    match flag.type:
        case "string-enum" | "list-of-string-enum":
            # We don't have a type map for string enum types as we don't
            # know the enum class at generation time, so we build it dynamically
            if flag.choices is None:
                raise ValueError(
                    "choices are required for string-enum and list-of-string-enum"
                )
            # Determine if the base type of the list is string or Choice
            if all(type(choice) is Choice for choice in flag.choices):
                # map the identifiers to the human-readbale values for the enum
                choices = {v.title: v.value for v in cast(list[Choice], flag.choices)}

            else:
                # for strings, use each string as the identifier and human
                # readable value
                choices = {v.upper(): v for v in cast(list[str], flag.choices)}
            # Create the base enum class with the wrap validator
            enum_cls = cast(type[Enum], StrEnum(f"{label}Enum", choices))
            base_type = Annotated[enum_cls, WrapValidator(enum_member(enum_cls))]

            if flag.type == "list-of-string-enum":
                py_type = (
                    list[base_type] if flag.required else Optional[list[base_type]]
                )
            else:
                py_type = base_type if flag.required else Optional[base_type]
        case "url" | "list-of-url":
            base_type = SecretUrl if flag.secret else SkipableUrl
            if flag.type == "list-of-url":
                py_type = (
                    list[base_type] if flag.required else Optional[list[base_type]]
                )
            else:
                py_type = base_type if flag.required else Optional[base_type]
        case "string" | "list-of-string":
            base_type = ZIMSecretStr if flag.secret else NotEmptyString
            if flag.type == "list-of-string":
                py_type = (
                    list[base_type] if flag.required else Optional[list[base_type]]
                )
            else:
                py_type = base_type if flag.required else Optional[base_type]

        case _:
            # For other simple types, we can just return the pydantic field with the
            # skip_validation wrapper
            py_type = (
                TYPE_MAP[flag.type] if flag.required else Optional[TYPE_MAP[flag.type]]
            )

    # For secret fields, we use the already defined ZIMSecretStr type
    # and it's variants since it supports secret values and masking based on context
    if flag.secret:
        return Annotated[py_type, pydantic_field]
    else:
        return Annotated[py_type, pydantic_field, WrapValidator(skip_validation)]


def build_offliner_model(
    *,
    model_name: str,
    offliner_id: str,
    schema: OfflinerSchema,
    base_model_cls: type[BaseModel] | type[DashModel] | type[CamelModel],
    validators: dict[str, Callable[[Any, ValidationInfo], Any]] | None = None,
):
    fields: dict[str, Annotated[Any, Any]] = {}
    for flag_name, flag_schema in schema.flags.items():
        fields[flag_name] = generate_field_type(flag_schema, flag_name)
    # Add the offliner_id field to the model with the base model class which
    # typically defines the alias generators and necessary config for the model
    return create_model(
        model_name,
        offliner_id=(Literal[offliner_id], Field(alias="offliner_id")),
        __base__=base_model_cls,
        __validators__=validators,
        **fields,
    )
