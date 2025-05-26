from typing import Annotated

from pydantic import AfterValidator, Field
from pydantic.types import AnyUrl, SecretStr


def no_null_char(value: str) -> str:
    """Validate that string value does not contains Unicode null character"""
    if "\u0000" in value:
        raise ValueError("Null character is not allowed")

    return value


NoNullCharString = Annotated[str, AfterValidator(no_null_char)]


def not_empty(value: str) -> str:
    """Validate that string value is not empty"""
    if not value.strip():
        raise ValueError("String value cannot be empty")

    return value


NotEmptyString = Annotated[NoNullCharString, AfterValidator(not_empty)]


Percentage = Annotated[int, Field(ge=1, le=100)]


def validate_optimization_cache(v: SecretStr | str) -> SecretStr:
    url = v.get_secret_value() if isinstance(v, SecretStr) else v
    AnyUrl.validate(url)
    return SecretStr(url)


S3OptimizationCache = Annotated[SecretStr, AfterValidator(validate_optimization_cache)]

ZIMLongDescription = Annotated[str, Field(max_length=4000)]

ZIMTitle = Annotated[str, Field(max_length=30)]

ZIMDescription = Annotated[str, Field(max_length=80)]

ZIMFileName = Annotated[
    str, Field(pattern=r"^(.+?_)([a-z\-]{2,3}?_)(.+_|)([\d]{4}-[\d]{2}|{period}).zim$")
]

SlackTarget = Annotated[str, Field(pattern=r"^[#|@].+$")]

ZIMPlatformValue = Annotated[int, Field(ge=0)]

ZIMLangCode = Annotated[str, Field(min_length=2, max_length=3)]

ZIMOutputFolder = Annotated[str, Field(pattern=r"^/output$")]

ZIMCPU = Annotated[int, Field(ge=0)]

ZIMMemory = Annotated[int, Field(ge=0)]

ZIMDisk = Annotated[int, Field(ge=0)]

SkipField = Annotated[int, Field(default=0, ge=0)]

LimitFieldMax500 = Annotated[int, Field(default=20, ge=0, le=500)]

LimitFieldMax200 = Annotated[int, Field(default=20, ge=0, le=200)]

PriorityField = Annotated[int, Field(default=0, ge=0, le=10)]

WorkerField = Annotated[NotEmptyString, Field(min_length=3)]


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
