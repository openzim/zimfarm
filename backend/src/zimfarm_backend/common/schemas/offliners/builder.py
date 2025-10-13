# ruff: noqa: UP007
from collections.abc import Callable
from enum import Enum, StrEnum
from itertools import chain
from typing import Annotated, Any, Literal, Optional, cast

from pydantic import (
    EmailStr,
    Field,
    WrapValidator,
    create_model,
    field_validator,
    model_validator,
)

from zimfarm_backend import logger
from zimfarm_backend.common.constants import getenv, parse_bool
from zimfarm_backend.common.schemas import CamelModel, DashModel
from zimfarm_backend.common.schemas.fields import (
    NotEmptyString,
    OptionalField,
    SecretUrl,
    SkipableBool,
    SkipableUrl,
    ZIMSecretStr,
    enum_member,
    skip_validation,
    validate_comma_separated_zim_lang_code,
)
from zimfarm_backend.common.schemas.offliners.models import (
    Choice,
    FlagSchema,
    OfflinerSpecSchema,
)
from zimfarm_backend.common.schemas.offliners.transformers import transform_data
from zimfarm_backend.common.schemas.offliners.validators import (
    check_exclusive_fields,
    validate_ted_links,
)
from zimfarm_backend.common.schemas.orms import OfflinerSchema

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


def get_field_validator(validator_name: str):
    match validator_name:
        case "language_code":
            return validate_comma_separated_zim_lang_code
        case "validate_ted_links":
            return validate_ted_links
        case _:
            raise ValueError(f"No validator functions registered for '{validator_name}")


def get_model_validator(validator_name: str):
    match validator_name:
        case "check_exclusive_fields":
            return check_exclusive_fields
        case _:
            raise ValueError(f"No validator functions registered for '{validator_name}")


def get_base_model_cls(base_model: str) -> type[CamelModel] | type[DashModel]:
    match base_model:
        case "DashModel":
            return DashModel
        case "CamelModel":
            return CamelModel
        case _:
            raise ValueError(f"'{base_model}' is not a known model")


def generate_field_type(offliner: str, flag: FlagSchema, label: str):
    """Generate the type for a flag with necessary metadata in annotations"""
    # Build up the pydantic field with necessary metadata
    use_relaxed_schema = parse_bool(
        getenv(f"{offliner.upper()}_USE_RELAXED_SCHEMA", default="false")
    )
    pydantic_field_cls = Field if flag.required else OptionalField
    pydantic_field = pydantic_field_cls(
        title=flag.title,
        description=flag.description,
        alias=flag.alias,
        ge=(flag.relaxed_min if flag.relaxed_min and use_relaxed_schema else flag.min),
        le=(flag.relaxed_max if flag.relaxed_max and use_relaxed_schema else flag.max),
        pattern=(
            flag.relaxed_pattern
            if flag.relaxed_pattern and use_relaxed_schema
            else flag.pattern
        ),
        min_length=(
            flag.relaxed_min_length
            if flag.relaxed_min_length and use_relaxed_schema
            else flag.min_length
        ),
        max_length=(
            flag.relaxed_max_length
            if flag.relaxed_max_length and use_relaxed_schema
            else flag.max_length
        ),
        # if a field is required and no default is specified, use ellipsis ...
        # otherwise, it invalidates the required validation
        default=... if flag.required and flag.default is None else flag.default,
        frozen=parse_bool(flag.frozen),
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


def generate_similarity_data(
    flags: dict[str, Any], offliner: OfflinerSchema, spec: OfflinerSpecSchema
) -> list[str]:
    """Generate the similarity list of flags data."""
    schema_cls = build_offliner_model(offliner, spec)
    result: list[list[str]] = []
    for similarity_data in spec.similarity_data:
        # find the pydantic field info from the schema class
        field_info = schema_cls.model_fields[similarity_data.flag]
        # find the value of the flag in the data. This is typically at the alias of the
        # field given we always dump with aliases. Sometimes, it turns out to be at the
        # name of the python identifier because we originally dumped without aliases.
        value: Any | None = None
        if field_info.alias:
            value = flags.get(field_info.alias, flags.get(similarity_data.flag))
        else:
            value = flags.get(similarity_data.flag)

        if value is None:
            logger.warning(
                f"Could not find value in data that matched the keys: "
                f"'{field_info.alias}', '{similarity_data.flag}'"
            )
            continue
        result.append(transform_data([value], similarity_data.transformers))
    return list(set(chain.from_iterable(result)))


def build_offliner_model(
    offliner: OfflinerSchema,
    schema: OfflinerSpecSchema,
):
    fields: dict[str, Annotated[Any, Any]] = {}
    for flag_name, flag_schema in schema.flags.items():
        fields[flag_name] = generate_field_type(offliner.id, flag_schema, flag_name)
    # Add the offliner_id field to the model with the base model class which
    # typically defines the alias generators and necessary config for the model
    field_validators = {
        f"{flag}_validator": field_validator(flag)(
            get_field_validator(flag_schema.custom_validator)
        )
        for flag, flag_schema in schema.flags.items()
        if flag_schema.custom_validator
    }
    model_validators: dict[str, Callable[..., Any]] = (
        {  # pyright: ignore[reportAssignmentType]
            f"{validator.name}_validator": model_validator(mode="after")(
                get_model_validator(validator.name)(validator.fields)
            )
            for validator in schema.model_validators
        }
    )
    return create_model(
        f"{offliner.id}FlagsSchema",
        offliner_id=(Literal[offliner.id], Field(alias="offliner_id")),
        __base__=get_base_model_cls(offliner.base_model),
        __validators__={**field_validators, **model_validators},
        **fields,
    )
