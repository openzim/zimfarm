from typing import Any

import pytest
from pydantic import AnyUrl, EmailStr, SecretStr

from zimfarm_backend.common.enums import TaskStatus
from zimfarm_backend.common.schemas.fields import (
    OptionalNotEmptyString,
    OptionalSecretUrl,
    OptionalZIMDescription,
    OptionalZIMLongDescription,
    OptionalZIMOutputFolder,
    OptionalZIMSecretStr,
    OptionalZIMTitle,
    SecretUrl,
)
from zimfarm_backend.common.schemas.offliners.mwoffliner import (
    MWOfflinerFlagsSchema,
    MWOfflinerFormatFlavour,
)
from zimfarm_backend.common.schemas.offliners.serializer import (
    get_enum_choices,
    get_field_type,
    is_secret,
    schema_to_flags,
)


@pytest.mark.parametrize(
    "field_type,expected_type",
    [
        (int, "integer"),
        (str, "string"),
        (bool, "boolean"),
        (AnyUrl, "url"),
        (EmailStr, "email"),
        (SecretStr, "string"),
        (OptionalNotEmptyString, "string"),
        (OptionalZIMOutputFolder, "string"),
        (OptionalZIMSecretStr, "string"),
        (TaskStatus, "string-enum"),
        (MWOfflinerFormatFlavour, "string-enum"),
        (list[int], "list-of-integer"),
        (list[str], "list-of-string"),
        (list[bool], "list-of-boolean"),
        (list[MWOfflinerFormatFlavour], "list-of-string-enum"),
    ],
)
def test_get_field_type(field_type: Any, expected_type: str):
    assert get_field_type(field_type) == expected_type


@pytest.mark.parametrize(
    "field_type,expected_choices",
    (
        (TaskStatus, [choice.value for choice in TaskStatus]),
        (list[TaskStatus], [choice.value for choice in TaskStatus]),
        (MWOfflinerFormatFlavour, [choice.value for choice in MWOfflinerFormatFlavour]),
        (
            list[MWOfflinerFormatFlavour],
            [choice.value for choice in MWOfflinerFormatFlavour],
        ),
    ),
)
def test_get_enum_choices(field_type: Any, expected_choices: list[str]):
    choices = [choice["value"] for choice in get_enum_choices(field_type)]
    assert len(choices) == len(expected_choices)
    for choice in choices:
        assert choice in expected_choices


@pytest.mark.parametrize(
    "field,is_secret_field",
    (
        pytest.param(TaskStatus, False, id="TaskStatus"),
        pytest.param(SecretStr, True, id="SecretStr"),
        pytest.param(OptionalZIMOutputFolder, False, id="OptionalZIMOutputFolder"),
        pytest.param(OptionalZIMSecretStr, True, id="OptionalZIMSecretStr"),
        pytest.param(OptionalNotEmptyString, False, id="OptionalNotEmptyString"),
        pytest.param(OptionalZIMDescription, False, id="OptionalZIMDescription"),
        pytest.param(
            OptionalZIMLongDescription, False, id="OptionalZIMLongDescription"
        ),
        pytest.param(OptionalZIMTitle, False, id="OptionalZIMTitle"),
        pytest.param(OptionalSecretUrl, True, id="OptionalSecretUrl"),
        pytest.param(SecretUrl, True, id="SecretUrl"),
    ),
)
def test_is_secret(field: Any, *, is_secret_field: bool):
    assert is_secret(field) == is_secret_field


def test_schema_to_flags():
    flags = schema_to_flags(MWOfflinerFlagsSchema)
    for flag in flags["flags"]:
        key = flag["key"]

        # Check if the flag is required
        if key in (
            "mwUrl",
            "adminEmail",
        ):
            assert flag["required"]
        else:
            assert not flag["required"]

        # Check if the flag is secret
        if key in ("mwPassword", "optimisationCacheUrl"):
            assert flag["secret"]
        else:
            assert "secret" not in flag

        if key in ("format",):
            assert flag["type"] == "list-of-string-enum"
            assert "choices" in flag
        elif key in ("customFlavour", "verbose", "forceRender"):
            assert flag["type"] == "string-enum"
            assert "choices" in flag
        elif key in ("adminEmail",):
            assert flag["type"] == "email"
            assert "choices" not in flag
        elif key in (
            "getCategories",
            "keepEmptyParagraphs",
            "minifyHtml",
            "webp",
            "insecure",
            "withoutZimFullTextIndex",
        ):
            assert flag["type"] == "boolean"
            assert "choices" not in flag
        elif key in ("requestTimeout",):
            assert flag["type"] == "integer"
            assert "choices" not in flag
        elif key in ("speed",):
            assert flag["type"] == "float"
            assert "choices" not in flag
        elif key in ("mwUrl", "articleList", "articleListToIgnore", "customZimFavicon"):
            assert flag["type"] == "url"
            assert "choices" not in flag
        else:
            assert flag["type"] == "string"
            assert "choices" not in flag
