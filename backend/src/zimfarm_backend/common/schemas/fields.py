from typing import Annotated, Any

from pydantic import AfterValidator, AnyUrl, Field, SecretStr, WrapSerializer
from pydantic_core.core_schema import SerializationInfo

from zimfarm_backend.common.enums import WarehousePath


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

Percentage = Annotated[int, Field(gt=0, le=100)]


OptionalPercentage = Percentage | None


def validate_optimization_cache(v: ZIMSecretStr | str) -> ZIMSecretStr:
    url = v.get_secret_value() if isinstance(v, SecretStr) else v
    AnyUrl(url)

    return SecretStr(url)


S3OptimizationCache = Annotated[
    ZIMSecretStr, AfterValidator(validate_optimization_cache)
]

OptionalS3OptimizationCache = S3OptimizationCache | None

ZIMLongDescription = Annotated[str, Field(max_length=4000)]

OptionalZIMLongDescription = ZIMLongDescription | None

ZIMTitle = Annotated[str, Field(max_length=30)]

OptionalZIMTitle = ZIMTitle | None

ZIMDescription = Annotated[str, Field(max_length=80)]

OptionalZIMDescription = ZIMDescription | None

ZIMFileName = Annotated[
    str,
    Field(pattern=r"^(.+?_)([a-z\-]{2,3}?_)(.+_|)([\d]{4}-[\d]{2}|\{period\}).zim$"),
]

OptionalZIMFileName = ZIMFileName | None

SlackTarget = Annotated[str, Field(pattern=r"^[#|@].+$")]

OptionalSlackTarget = SlackTarget | None

ZIMPlatformValue = Annotated[int, Field(gt=0)]


OptionalZIMPlatformValue = ZIMPlatformValue | None

ZIMLangCode = Annotated[str, Field(min_length=2, max_length=8)]

OptionalZIMLangCode = ZIMLangCode | None

ZIMOutputFolder = Annotated[str, Field(pattern=r"^/output$")]

OptionalZIMOutputFolder = ZIMOutputFolder | None

ZIMProgressFile = Annotated[
    NotEmptyString, Field(pattern=r"^/output/task_progress\.json$")
]

OptionalZIMProgressFile = ZIMProgressFile | None

ZIMCPU = Annotated[int, Field(gt=0)]

OptionalZIMCPU = ZIMCPU | None

ZIMMemory = Annotated[int, Field(gt=0)]

OptionalZIMMemory = ZIMMemory | None

ZIMDisk = Annotated[int, Field(gt=0)]

OptionalZIMDisk = ZIMDisk | None

SkipField = Annotated[int, Field(default=0, ge=0)]

OptionalSkipField = SkipField | None

LimitFieldMax500 = Annotated[int, Field(default=20, gt=0, le=500)]

OptionalLimitFieldMax500 = LimitFieldMax500 | None

LimitFieldMax200 = Annotated[int, Field(default=20, gt=0, le=200)]

OptionalLimitFieldMax200 = LimitFieldMax200 | None

PriorityField = Annotated[int, Field(default=1, gt=0, le=10)]


OptionalPriorityField = PriorityField | None

WorkerField = Annotated[NotEmptyString, Field(min_length=3)]

OptionalWorkerField = WorkerField | None


def validate_schedule_name(name: str) -> str:
    """
    Validate name is not empty and does not contain leading and/or trailing space(s)
    """
    if name == "none":
        raise ValueError("`none` is a restricted keyword")
    if not name.strip() or name != name.strip():
        raise ValueError("Recipe name cannot contain leading and/or trailing space(s)")
    return name


ScheduleNameField = Annotated[NotEmptyString, AfterValidator(validate_schedule_name)]

OptionalScheduleNameField = ScheduleNameField | None


def validate_warehouse_path(warehouse_path: str) -> str:
    """Validate that the string is a valid warehouse path."""
    if warehouse_path not in WarehousePath.all():
        raise ValueError(f"{warehouse_path} is not a valid Warehouse path")
    return warehouse_path


WarehousePathField = Annotated[str, AfterValidator(validate_warehouse_path)]
