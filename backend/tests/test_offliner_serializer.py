from typing import Any

import pytest
from pydantic import BaseModel

from zimfarm_backend.common.enums import TaskStatus
from zimfarm_backend.common.schemas.offliners.serializer import (
    get_enum_choices,
    schema_to_flags,
)


@pytest.mark.parametrize(
    "field_type,expected_choices",
    (
        (TaskStatus, [choice.value for choice in TaskStatus]),
        (list[TaskStatus], [choice.value for choice in TaskStatus]),
    ),
)
def test_get_enum_choices(field_type: Any, expected_choices: list[str]):
    choices = [choice.value for choice in get_enum_choices(field_type)]
    assert len(choices) == len(expected_choices)
    for choice in choices:
        assert choice in expected_choices


def test_mw_offliner_schema_to_flags(mwoffliner_schema_cls: type[BaseModel]):
    flags = schema_to_flags(mwoffliner_schema_cls)
    for flag in flags:
        key = flag.data_key

        # Check if the flag is required
        if key in (
            "mwUrl",
            "adminEmail",
        ):
            assert flag.required
        else:
            assert not flag.required

        # Check if the flag is secret
        if key in ("mwPassword", "optimisationCacheUrl"):
            assert flag.secret
        else:
            assert not flag.secret

        if key in ("format",):
            assert flag.type == "list-of-string-enum"
            assert flag.choices is not None
        elif key in ("customFlavour", "verbose", "forceRender"):
            assert flag.type == "string-enum"
            assert flag.choices is not None
        elif key in ("adminEmail",):
            assert flag.type == "email"
            assert flag.choices is None
        elif key in (
            "getCategories",
            "keepEmptyParagraphs",
            "minifyHtml",
            "webp",
            "insecure",
            "withoutZimFullTextIndex",
        ):
            assert flag.type == "boolean"
            assert flag.choices is None
        elif key in ("requestTimeout",):
            assert flag.type == "integer"
            assert flag.choices is None
        elif key in ("speed",):
            assert flag.type == "float"
            assert flag.choices is None
        elif key in ("mwUrl", "customZimFavicon", "optimisationCacheUrl"):
            assert flag.type == "url"
            assert flag.choices is None
        else:
            assert flag.type == "string"
            assert flag.choices is None

        # Validat that restrictions are correctly inferred
        if key in ("customZIMTitle",):
            assert flag.min_graphemes == 1
            assert flag.max_graphemes == 30
        elif key in ("customZIMDescription",):
            assert flag.min_graphemes == 1
            assert flag.max_graphemes == 80
        elif key in ("customZIMLongDescription",):
            assert flag.min_graphemes == 1
            assert flag.max_graphemes == 4000
        elif key in ("outputDirectory",):
            assert flag.pattern is not None
