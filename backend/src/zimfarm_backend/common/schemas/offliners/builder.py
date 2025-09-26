# ruff: noqa: UP007
from collections.abc import Callable
from enum import Enum, StrEnum
from typing import Annotated, Any, Literal, Optional, Self, cast

from pydantic import (
    ConfigDict,
    EmailStr,
    Field,
    WrapValidator,
    create_model,
    field_validator,
    model_validator,
)

from zimfarm_backend.common.constants import OFFLINERS_WITH_RELAXED_SCHEMAS, parse_bool
from zimfarm_backend.common.enums import Offliner
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
    validate_comma_separated_zim_lang_code,
)
from zimfarm_backend.common.schemas.offliners.models import (
    BaseFlagSchema,
    Choice,
)
from zimfarm_backend.common.schemas.offliners.validators import (
    check_exclusive_fields,
    validate_ted_links,
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
    relaxed_pattern: str | None = Field(validation_alias="relaxedPattern", default=None)
    relaxed_min: int | None = Field(validation_alias="relaxedMin", default=None)
    relaxed_max: int | None = Field(validation_alias="relaxedMax", default=None)
    relaxed_min_length: int | None = Field(
        validation_alias="relaxedMinLength", default=None
    )
    relaxed_max_length: int | None = Field(
        validation_alias="relaxedMaxLength", default=None
    )
    custom_validator: str | None = Field(
        validation_alias="customValidator", default=None
    )
    default: str | None = None
    frozen: bool | None = None

    @model_validator(mode="after")
    def check_frozen_fields(self) -> Self:
        """Validate that a frozen field has a default"""
        if self.frozen and not self.default:
            raise ValueError("Frozen fields should have a default")

        return self

    # disallow extra fields so that we fail early validation time. Helps with cases
    # where we mistype a value in the schema rather than the field being omitted which
    # is a harder issue to track
    model_config = ConfigDict(extra="forbid")


class ModelValidatorSchema(CamelModel):
    """Schema for defining the validators that should apply at the model level"""

    name: str  # name of the validator function
    fields: list[str]  # list of field names to call the function with
    model_config = ConfigDict(extra="forbid")


class OfflinerSchema(CamelModel):
    flags: dict[str, FlagSchema]
    model_validators: list[ModelValidatorSchema] = Field(  # pyright: ignore
        default_factory=list,
    )


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


def generate_field_type(offliner: Offliner, flag: FlagSchema, label: str):
    """Generate the type for a flag with necessary metadata in annotations"""
    # Build up the pydantic field with necessary metadata
    pydantic_field_cls = Field if flag.required else OptionalField
    pydantic_field = pydantic_field_cls(
        title=flag.title,
        description=flag.description,
        alias=flag.alias,
        ge=(
            flag.relaxed_min
            if flag.relaxed_min and offliner in OFFLINERS_WITH_RELAXED_SCHEMAS
            else flag.min
        ),
        le=(
            flag.relaxed_max
            if flag.relaxed_max and offliner in OFFLINERS_WITH_RELAXED_SCHEMAS
            else flag.max
        ),
        pattern=(
            flag.relaxed_pattern
            if flag.relaxed_pattern and offliner in OFFLINERS_WITH_RELAXED_SCHEMAS
            else flag.pattern
        ),
        min_length=(
            flag.relaxed_min_length
            if flag.relaxed_min_length and offliner in OFFLINERS_WITH_RELAXED_SCHEMAS
            else flag.min_length
        ),
        max_length=(
            flag.relaxed_max_length
            if flag.relaxed_max_length and offliner in OFFLINERS_WITH_RELAXED_SCHEMAS
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


def build_offliner_model(
    *,
    model_name: str,
    offliner_id: Offliner,
    schema: OfflinerSchema,
    base_model_cls: type[BaseModel] | type[DashModel] | type[CamelModel],
):
    fields: dict[str, Annotated[Any, Any]] = {}
    for flag_name, flag_schema in schema.flags.items():
        fields[flag_name] = generate_field_type(offliner_id, flag_schema, flag_name)
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
        model_name,
        offliner_id=(Literal[offliner_id], Field(alias="offliner_id")),
        __base__=base_model_cls,
        __validators__={**field_validators, **model_validators},
        **fields,
    )
