from collections.abc import Callable
from enum import Enum
from typing import Annotated, Any

import pycountry
import regex
from pydantic import (
    AfterValidator,
    AnyUrl,
    Field,
    SecretStr,
    ValidationInfo,
    ValidatorFunctionWrapHandler,
    WrapSerializer,
    WrapValidator,
)
from pydantic_core.core_schema import SerializationInfo

from zimfarm_backend.common.enums import Platform, WarehousePath


class GraphemeStr(str):
    def __len__(self) -> int:
        # Count the number of grapheme clusters
        return len(regex.findall(r"\X", self))


def to_grapheme_str(value: str):
    return GraphemeStr(value)


def no_null_char(value: str) -> str:
    """Validate that string value does not contains Unicode null character"""
    if "\u0000" in value:
        raise ValueError("Null character is not allowed")

    return value


def OptionalField(**kwargs: Any) -> Any:  # noqa N802
    kwargs.update({"default": None})
    return Field(**kwargs)


NoNullCharString = Annotated[
    str, AfterValidator(no_null_char), AfterValidator(to_grapheme_str)
]


OptionalNoNullCharString = NoNullCharString | None


def not_empty(value: str) -> str:
    """Validate that string value is not empty"""
    if not value.strip():
        raise ValueError("String value cannot be empty")

    return value


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

OptionalNotEmptyString = NotEmptyString | None

ZIMMetadataString = Annotated[
    str,
    AfterValidator(no_null_char),
    AfterValidator(not_empty),
    AfterValidator(to_grapheme_str),
]


def show_secrets(value: Any, handler: Any, info: SerializationInfo) -> Any:
    """Show secret values in serialization"""
    context = info.context
    if context and context.get("show_secrets"):
        if isinstance(value, SecretStr):
            return value.get_secret_value()
    return handler(value, info)


def skip_validation(
    value: Any, handler: ValidatorFunctionWrapHandler, info: ValidationInfo
) -> Any:
    """Skip pydantic validation"""
    context = info.context
    if context and context.get("skip_validation"):
        return value
    return handler(value)


ZIMSecretStr = Annotated[SecretStr, WrapSerializer(show_secrets)]

OptionalZIMSecretStr = ZIMSecretStr | None

Percentage = Annotated[int, Field(ge=1, le=100), WrapValidator(skip_validation)]


OptionalPercentage = Percentage | None


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

OptionalSecretUrl = SecretUrl | None

SkipableUrl = Annotated[AnyUrl, WrapValidator(skip_validation)]
OptionalSkipableUrl = SkipableUrl | None

ZIMLongDescription = Annotated[
    ZIMMetadataString,
    Field(min_length=1, max_length=4000),
    WrapValidator(skip_validation),
]

OptionalZIMLongDescription = ZIMLongDescription | None

ZIMTitle = Annotated[
    ZIMMetadataString,
    Field(min_length=1, max_length=30),
    WrapValidator(skip_validation),
]

OptionalZIMTitle = ZIMTitle | None

ZIMDescription = Annotated[
    ZIMMetadataString,
    Field(min_length=1, max_length=80),
    WrapValidator(skip_validation),
]

OptionalZIMDescription = ZIMDescription | None

ZIMFileName = Annotated[
    str,
    Field(
        pattern=r"^([a-z0-9\-\.]+_)([a-z\-]+_)([a-z0-9\-\.]+_)([a-z0-9\-\.]+_|)([\d]{4}-[\d]{2}|\{period\}).zim$"
    ),
    WrapValidator(skip_validation),
]

OptionalZIMFileName = ZIMFileName | None

SlugString = Annotated[
    str,
    Field(
        pattern=r"^[A-Za-z0-9._-]+$",
    ),
    WrapValidator(skip_validation),
]

OptionalSlugString = SlugString | None

ZIMName = Annotated[
    str,
    Field(pattern=r"^([a-z0-9\-\.]+_)([a-z\-]+_)([a-z0-9\-\.]+)$"),
    WrapValidator(skip_validation),
]

OptionalZIMName = ZIMName | None

SlackTarget = Annotated[
    str, Field(pattern=r"^[#|@].+$"), WrapValidator(skip_validation)
]

OptionalSlackTarget = SlackTarget | None

ZIMPlatformValue = Annotated[int, Field(ge=1), WrapValidator(skip_validation)]

OptionalZIMPlatformValue = ZIMPlatformValue | None

ZIMLangCode = Annotated[
    str,
    Field(min_length=3, max_length=3),
    WrapValidator(skip_validation),
    AfterValidator(validate_language_code),
]

CommaSeparatedZIMLangCode = Annotated[
    str,
    Field(pattern=r"^[a-z]{3}(,[a-z]{3})*$"),
    AfterValidator(validate_comma_separated_zim_lang_code),
    WrapValidator(skip_validation),
]

OptionalCommaSeparatedZIMLangCode = CommaSeparatedZIMLangCode | None

OptionalZIMLangCode = ZIMLangCode | None

ZIMOutputFolder = Annotated[
    str, Field(pattern=r"^/output$"), WrapValidator(skip_validation)
]

SkipableBool = Annotated[bool, WrapValidator(skip_validation)]
OptionalSkipableBool = SkipableBool | None

OptionalZIMOutputFolder = ZIMOutputFolder | None

ZIMProgressFile = Annotated[
    NotEmptyString,
    Field(pattern=r"^/output/task_progress\.json$"),
    WrapValidator(skip_validation),
]

OptionalZIMProgressFile = ZIMProgressFile | None

ZIMCPU = Annotated[int, Field(ge=0), WrapValidator(skip_validation)]

OptionalZIMCPU = ZIMCPU | None

ZIMMemory = Annotated[int, Field(ge=0), WrapValidator(skip_validation)]

OptionalZIMMemory = ZIMMemory | None

ZIMDisk = Annotated[int, Field(ge=0), WrapValidator(skip_validation)]

OptionalZIMDisk = ZIMDisk | None

SkipField = Annotated[int, Field(ge=0), WrapValidator(skip_validation)]

OptionalSkipField = SkipField | None

LimitFieldMax500 = Annotated[int, Field(ge=1, le=500), WrapValidator(skip_validation)]

OptionalLimitFieldMax500 = LimitFieldMax500 | None

LimitFieldMax200 = Annotated[int, Field(ge=1, le=200), WrapValidator(skip_validation)]

OptionalLimitFieldMax200 = LimitFieldMax200 | None

PriorityField = Annotated[int, Field(ge=1, le=10), WrapValidator(skip_validation)]

OptionalPriorityField = PriorityField | None

WorkerField = Annotated[
    NotEmptyString, Field(min_length=3), WrapValidator(skip_validation)
]

OptionalWorkerField = WorkerField | None


def validate_schedule_name(name: str, info: ValidationInfo) -> str:
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


ScheduleNameField = Annotated[NotEmptyString, AfterValidator(validate_schedule_name)]

OptionalScheduleNameField = ScheduleNameField | None


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

OptionalPlatformField = PlatformField | None
