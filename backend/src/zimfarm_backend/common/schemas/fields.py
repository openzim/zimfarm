from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Annotated, Any

import pycountry
import regex
from pydantic import (
    AfterValidator,
    AnyUrl,
    Field,
    SecretStr,
    SerializerFunctionWrapHandler,
    ValidationInfo,
    ValidatorFunctionWrapHandler,
    WrapSerializer,
    WrapValidator,
)
from pydantic_core.core_schema import SerializationInfo
from pydantic_extra_types.color import Color

from zimfarm_backend.common.constants import SECRET_STRING_LENGTH
from zimfarm_backend.common.enums import Platform, WarehousePath


@dataclass(frozen=True)
class GraphemeLength:
    min: int | None = None
    max: int | None = None

    def __call__(self, v: str, info: ValidationInfo) -> str:
        context = info.context
        if context and context.get("skip_validation"):
            return v

        n = len(regex.findall(r"\X", v))
        if self.min is not None and n < self.min:
            raise ValueError(
                f"String should have at least {self.min} grapheme clusters (got {n})"
            )
        if self.max is not None and n > self.max:
            raise ValueError(
                f"String should have at most {self.max} grapheme clusters (got {n})"
            )
        return v


def no_null_char(value: str) -> str:
    """Validate that string value does not contains Unicode null character"""
    if "\u0000" in value:
        raise ValueError("Null character is not allowed")

    return value


def OptionalField(**kwargs: Any) -> Any:  # noqa N802
    kwargs.update({"default": None})
    return Field(**kwargs)


NoNullCharString = Annotated[
    str,
    AfterValidator(no_null_char),
]


def not_empty(value: str) -> str:
    """Validate that string value is not empty"""
    if not value.strip():
        raise ValueError("String value cannot be empty")

    # cast value to str else Field validators will use the str len method for
    # length validation
    return value.strip()


def validate_language_code(value: str | None, info: ValidationInfo) -> str | None:
    """Validate that string is a valid ISO-693-3 language code"""
    if value is None:
        return value
    context = info.context
    if context and context.get("skip_validation"):
        return value
    if pycountry.languages.get(alpha_3=value):
        return value
    raise ValueError(
        f"Language code '{value}' is not a recognized ISO-639-3 language code"
    )


def validate_comma_separated_zim_lang_code(
    value: str | None, info: ValidationInfo
) -> str | None:
    """Validate that string is a comma separated list of ISO-693-3 language codes"""
    if value is None:
        return value
    for lang_code in value.split(","):
        validate_language_code(lang_code, info)
    return value


def enum_member(
    enum_cls: type[Enum],
) -> Callable[[Any, ValidatorFunctionWrapHandler, ValidationInfo], Any]:
    """Validate that a value is an enum member."""

    def _validate(
        value: Any, handler: ValidatorFunctionWrapHandler, info: ValidationInfo
    ) -> Any:
        context = info.context
        if context and context.get("skip_validation"):
            return value
        allowed_values = {e.value for e in enum_cls}
        if value not in allowed_values:
            raise ValueError(
                f"Value must be one of {', '.join(allowed_values)}, got {value}"
            )
        return handler(value)

    return _validate


NotEmptyString = Annotated[NoNullCharString, AfterValidator(not_empty)]


def show_secrets(value: Any, _: Any, info: SerializationInfo) -> Any:
    """Show secret values in serialization"""
    context = info.context
    value = value if isinstance(value, SecretStr) else SecretStr(value)
    if context and context.get("show_secrets"):
        value = value.get_secret_value()
    else:
        value = "*" * SECRET_STRING_LENGTH
    return value


def skip_validation(
    value: Any, handler: ValidatorFunctionWrapHandler, info: ValidationInfo
) -> Any:
    """Skip pydantic validation"""
    context = info.context
    if context and context.get("skip_validation"):
        return value
    return handler(value)


ZIMSecretStr = Annotated[SecretStr, WrapSerializer(show_secrets)]


Percentage = Annotated[int, Field(ge=1, le=100), WrapValidator(skip_validation)]


def validate_secret_url(v: ZIMSecretStr | str, info: ValidationInfo) -> ZIMSecretStr:
    url = v.get_secret_value() if isinstance(v, SecretStr) else v
    context = info.context
    if context and context.get("skip_validation"):
        # even though we are not validating it, we still want it to be a secret string
        return SecretStr(url)

    # validate the URL
    AnyUrl(url)

    return SecretStr(url)


SecretUrl = Annotated[ZIMSecretStr, AfterValidator(validate_secret_url)]


SkipableUrl = Annotated[AnyUrl, WrapValidator(skip_validation)]


SlackTarget = Annotated[
    str, Field(pattern=r"^[#|@].+$"), WrapValidator(skip_validation)
]


ZIMLangCode = Annotated[
    str,
    Field(min_length=3, max_length=3),
    WrapValidator(skip_validation),
    AfterValidator(validate_language_code),
]


SkipableBool = Annotated[bool, WrapValidator(skip_validation)]


def serialize_color_to_hex(value: Any, _: SerializerFunctionWrapHandler) -> str:
    """Serialize a color to hexadecimal codes."""
    if isinstance(value, Color):
        value = value.as_hex(format="long").upper()
    return value


SkipableColor = Annotated[
    Color, WrapValidator(skip_validation), WrapSerializer(serialize_color_to_hex)
]


ZIMCPU = Annotated[int, Field(ge=0), WrapValidator(skip_validation)]


ZIMMemory = Annotated[int, Field(ge=0), WrapValidator(skip_validation)]


ZIMDisk = Annotated[int, Field(ge=0), WrapValidator(skip_validation)]


SkipField = Annotated[int, Field(ge=0), WrapValidator(skip_validation)]


LimitFieldMax500 = Annotated[int, Field(ge=1, le=500), WrapValidator(skip_validation)]


LimitFieldMax200 = Annotated[int, Field(ge=1, le=200), WrapValidator(skip_validation)]


PriorityField = Annotated[int, Field(ge=1, le=10), WrapValidator(skip_validation)]


WorkerField = Annotated[
    NotEmptyString, Field(min_length=3), WrapValidator(skip_validation)
]


def validate_recipe_name(name: str, info: ValidationInfo) -> str:
    """
    Validate name is not empty and does not contain leading and/or trailing space(s)
    """
    context = info.context
    if context and context.get("skip_validation"):
        return name
    if name == "none":
        raise ValueError("`none` is a restricted keyword")
    if not name.strip() or name != name.strip():
        raise ValueError("Recipe name cannot contain leading and/or trailing space(s)")
    if "/" in name:
        raise ValueError("Recipe name cannot contain slash")
    if any(char.isupper() for char in name):
        raise ValueError("Recipe name should only contain lower case characters")
    return name


RecipeNameField = Annotated[NotEmptyString, AfterValidator(validate_recipe_name)]


def validate_warehouse_path(warehouse_path: str, info: ValidationInfo) -> str:
    """Validate that the string is a valid warehouse path."""
    context = info.context
    if context and context.get("skip_validation"):
        return warehouse_path
    if warehouse_path not in WarehousePath.all():
        raise ValueError(f"{warehouse_path} is not a valid Warehouse path")
    return warehouse_path


WarehousePathField = Annotated[str, AfterValidator(validate_warehouse_path)]


def validate_platform_value(platform: str, info: ValidationInfo) -> str:
    context = info.context
    if context and context.get("skip_validation"):
        return platform
    if platform not in Platform.all():
        raise ValueError(f"{platform} is not a valid Platform")
    return platform


PlatformField = Annotated[str, AfterValidator(validate_platform_value)]
