import re
from collections.abc import Callable, Sized
from enum import Enum
from typing import Annotated, Any

import pycountry
from pydantic import (
    AfterValidator,
    AnyUrl,
    Field,
    SecretStr,
    ValidationInfo,
    ValidatorFunctionWrapHandler,
    WrapSerializer,
)
from pydantic_core.core_schema import SerializationInfo

from zimfarm_backend.common.enums import Platform, WarehousePath


def no_null_char(value: str) -> str:
    """Validate that string value does not contains Unicode null character"""
    if "\u0000" in value:
        raise ValueError("Null character is not allowed")

    return value


def OptionalField(**kwargs: Any) -> Any:  # noqa N802
    kwargs.update({"default": None})
    return Field(**kwargs)


NoNullCharString = Annotated[str, AfterValidator(no_null_char)]

OptionalNoNullCharString = NoNullCharString | None


def not_empty(value: str) -> str:
    """Validate that string value is not empty"""
    if not value.strip():
        raise ValueError("String value cannot be empty")

    return value


def between(
    *, low: int | None = None, high: int | None = None
) -> Callable[[int, ValidationInfo], int]:
    """Validate that value is between low and high (if set)"""

    def _validate(value: int, info: ValidationInfo):
        context = info.context
        if context and context.get("skip_validation"):
            return value
        if low is not None and value < low:
            raise ValueError(
                f"Value must be greater than or equal to {low}, got {value}"
            )
        if high is not None and value > high:
            raise ValueError(f"Value must be less than or equal to {high}, got {value}")
        return value

    return _validate


def validate_language_code(value: str, info: ValidationInfo) -> str:
    """Validate that string is a valid ISO-693-3 language code"""
    context = info.context
    if context and context.get("skip_validation"):
        return value
    if pycountry.languages.get(alpha_3=value):
        return value
    raise ValueError(
        f"Language code '{value}' is not a recognized ISO-639-3 language code"
    )


def length_between(
    *, low: int | None = None, high: int | None = None
) -> Callable[[Sized, ValidationInfo], Sized]:
    """Validate that length of value is between low and high"""

    def _validate(value: Sized, info: ValidationInfo):
        context = info.context
        if context and context.get("skip_validation"):
            return value
        if low is not None and len(value) < low:
            raise ValueError(
                f"Value must be greater than or equal to {low}, got {len(value)}"
            )
        if high is not None and len(value) > high:
            raise ValueError(
                f"Value must be less than or equal to {high}, got {len(value)}"
            )
        return value

    return _validate


def pattern(pattern: str) -> Callable[[str, ValidationInfo], str]:
    """Validate that value matches the pattern"""

    def _validate(value: str, info: ValidationInfo):
        context = info.context
        if context and context.get("skip_validation"):
            return value
        if not re.match(pattern, value):
            raise ValueError(f"Value must match the pattern {pattern}, got {value}")
        return value

    return _validate


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


def show_secrets(value: Any, handler: Any, info: SerializationInfo) -> Any:
    """Show secret values in serialization"""
    context = info.context
    if context and context.get("show_secrets"):
        if isinstance(value, SecretStr):
            return value.get_secret_value()
    return handler(value, info)


ZIMSecretStr = Annotated[SecretStr, WrapSerializer(show_secrets)]

OptionalZIMSecretStr = ZIMSecretStr | None

Percentage = Annotated[int, AfterValidator(between(low=1, high=100))]


OptionalPercentage = Percentage | None


def validate_secret_url(v: ZIMSecretStr | str) -> ZIMSecretStr:
    url = v.get_secret_value() if isinstance(v, SecretStr) else v
    AnyUrl(url)

    return SecretStr(url)


SecretUrl = Annotated[ZIMSecretStr, AfterValidator(validate_secret_url)]

OptionalSecretUrl = SecretUrl | None

ZIMLongDescription = Annotated[str, AfterValidator(length_between(low=1, high=4000))]

OptionalZIMLongDescription = ZIMLongDescription | None

ZIMTitle = Annotated[str, AfterValidator(length_between(low=1, high=30))]

OptionalZIMTitle = ZIMTitle | None

ZIMDescription = Annotated[str, AfterValidator(length_between(low=1, high=80))]

OptionalZIMDescription = ZIMDescription | None

ZIMFileName = Annotated[
    str,
    AfterValidator(
        pattern(
            r"^([a-z0-9\-\.]+_)([a-z\-]+_)([a-z0-9\-\.]+_)([a-z0-9\-\.]+_|)([\d]{4}-[\d]{2}|\{period\}).zim$"
        )
    ),
]

OptionalZIMFileName = ZIMFileName | None

ZIMName = Annotated[
    str,
    AfterValidator(pattern(r"^([a-z0-9\-\.]+_)([a-z\-]+_)([a-z0-9\-\.]+)$")),
]

OptionalZIMName = ZIMName | None

SlackTarget = Annotated[str, AfterValidator(pattern(r"^[#|@].+$"))]

OptionalSlackTarget = SlackTarget | None

ZIMPlatformValue = Annotated[int, AfterValidator(between(low=1))]

OptionalZIMPlatformValue = ZIMPlatformValue | None

ZIMLangCode = Annotated[
    str,
    AfterValidator(length_between(low=3, high=3)),
    AfterValidator(validate_language_code),
]

OptionalZIMLangCode = ZIMLangCode | None

ZIMOutputFolder = Annotated[str, AfterValidator(pattern(r"^/output$"))]

OptionalZIMOutputFolder = ZIMOutputFolder | None

ZIMProgressFile = Annotated[
    NotEmptyString, AfterValidator(pattern(r"^/output/task_progress\.json$"))
]

OptionalZIMProgressFile = ZIMProgressFile | None

ZIMCPU = Annotated[int, AfterValidator(between(low=1))]

OptionalZIMCPU = ZIMCPU | None

ZIMMemory = Annotated[int, AfterValidator(between(low=1))]

OptionalZIMMemory = ZIMMemory | None

ZIMDisk = Annotated[int, AfterValidator(between(low=1))]

OptionalZIMDisk = ZIMDisk | None

SkipField = Annotated[int, AfterValidator(between(low=0))]

OptionalSkipField = SkipField | None

LimitFieldMax500 = Annotated[int, AfterValidator(between(low=1, high=500))]

OptionalLimitFieldMax500 = LimitFieldMax500 | None

LimitFieldMax200 = Annotated[int, AfterValidator(between(low=1, high=200))]

OptionalLimitFieldMax200 = LimitFieldMax200 | None

PriorityField = Annotated[int, AfterValidator(between(low=1, high=10))]

OptionalPriorityField = PriorityField | None

WorkerField = Annotated[NotEmptyString, AfterValidator(length_between(low=3))]

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
