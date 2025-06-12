from typing import Annotated, Any

from pydantic import AfterValidator, AnyUrl, Field, SecretStr


def no_null_char(value: str) -> str:
    """Validate that string value does not contains Unicode null character"""
    if "\u0000" in value:
        raise ValueError("Null character is not allowed")

    return value


def OptionalField(**kwargs: Any) -> Any:  # noqa N802
    kwargs.update({"default": None})
    return Field(**kwargs)


NoNullCharString = Annotated[str, AfterValidator(no_null_char)]

type OptionalNoNullCharString = NoNullCharString | None


def not_empty(value: str) -> str:
    """Validate that string value is not empty"""
    if not value.strip():
        raise ValueError("String value cannot be empty")

    return value


NotEmptyString = Annotated[NoNullCharString, AfterValidator(not_empty)]

type OptionalNotEmptyString = NotEmptyString | None

type OptionalSecretStr = SecretStr | None

Percentage = Annotated[int, Field(gt=0, le=100)]


type OptionalPercentage = Percentage | None


def validate_optimization_cache(v: SecretStr | str) -> SecretStr:
    url = v.get_secret_value() if isinstance(v, SecretStr) else v
    AnyUrl(url)

    return SecretStr(url)


S3OptimizationCache = Annotated[SecretStr, AfterValidator(validate_optimization_cache)]

type OptionalS3OptimizationCache = S3OptimizationCache | None

ZIMLongDescription = Annotated[str, Field(max_length=4000)]

type OptionalZIMLongDescription = ZIMLongDescription | None

ZIMTitle = Annotated[str, Field(max_length=30)]

type OptionalZIMTitle = ZIMTitle | None

ZIMDescription = Annotated[str, Field(max_length=80)]

type OptionalZIMDescription = ZIMDescription | None

ZIMFileName = Annotated[
    str,
    Field(pattern=r"^(.+?_)([a-z\-]{2,3}?_)(.+_|)([\d]{4}-[\d]{2}|\{period\}).zim$"),
]

type OptionalZIMFileName = ZIMFileName | None

SlackTarget = Annotated[str, Field(pattern=r"^[#|@].+$")]

type OptionalSlackTarget = SlackTarget | None

ZIMPlatformValue = Annotated[int, Field(gt=0)]


type OptionalZIMPlatformValue = ZIMPlatformValue | None

ZIMLangCode = Annotated[str, Field(min_length=2, max_length=3)]

type OptionalZIMLangCode = ZIMLangCode | None

ZIMOutputFolder = Annotated[str, Field(pattern=r"^/output$")]

type OptionalZIMOutputFolder = ZIMOutputFolder | None

ZIMProgressFile = Annotated[
    NotEmptyString, Field(pattern=r"^/output/task_progress\.json$")
]

type OptionalZIMProgressFile = ZIMProgressFile | None

ZIMCPU = Annotated[int, Field(gt=0)]

type OptionalZIMCPU = ZIMCPU | None

ZIMMemory = Annotated[int, Field(gt=0)]

type OptionalZIMMemory = ZIMMemory | None

ZIMDisk = Annotated[int, Field(gt=0)]

type OptionalZIMDisk = ZIMDisk | None

SkipField = Annotated[int, Field(default=0, ge=0)]

type OptionalSkipField = SkipField | None

LimitFieldMax500 = Annotated[int, Field(default=20, gt=0, le=500)]

type OptionalLimitFieldMax500 = LimitFieldMax500 | None

LimitFieldMax200 = Annotated[int, Field(default=20, gt=0, le=200)]

type OptionalLimitFieldMax200 = LimitFieldMax200 | None

PriorityField = Annotated[int, Field(default=1, gt=0, le=10)]


type OptionalPriorityField = PriorityField | None

WorkerField = Annotated[NotEmptyString, Field(min_length=3)]

type OptionalWorkerField = WorkerField | None


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

type OptionalScheduleNameField = ScheduleNameField | None
