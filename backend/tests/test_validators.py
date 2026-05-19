# ruff: noqa: E501
# ruff: noqa: E501
from contextlib import nullcontext as does_not_raise
from typing import Any

import pydantic
import pytest
from _pytest.python_api import RaisesContext
from pydantic import ValidationError, create_model

from zimfarm_backend.common.constants import parse_bool
from zimfarm_backend.common.schemas import BaseModel, CamelModel
from zimfarm_backend.common.schemas.fields import (
    SecretUrl,
    SkipableBool,
    SkipableUrl,
)
from zimfarm_backend.common.schemas.offliners.builder import generate_field_type
from zimfarm_backend.common.schemas.offliners.models import FlagSchema


class SkipableBoolModel(BaseModel):
    value: SkipableBool


class SecretUrlModel(BaseModel):
    value: SecretUrl


class SkipableUrlModel(BaseModel):
    value: SkipableUrl


@pytest.mark.parametrize(
    "languages,expected",
    [
        pytest.param("eng,fra,jpn", does_not_raise(), id="valid_languages"),
        pytest.param(
            "en,fr,jp", pytest.raises(ValidationError), id="invalid_language_code"
        ),
    ],
)
def test_ted_flags_schema(
    ted_flags_schema_cls: type[pydantic.BaseModel],
    languages: str,
    expected: RaisesContext[Exception],
):
    with expected:
        ted_flags_schema_cls(
            name="ted-talks_mul_football",
            offliner_id="ted",
            languages=languages,
            topics="football",
        )


def test_ted_flags_schema_skips_validation_when_context_set(
    ted_flags_schema_cls: type[BaseModel],
):
    with does_not_raise():
        ted_flags_schema_cls.model_validate(
            {
                "name": "ted-talks_mul_football",
                "offliner_id": "ted",
                "languages": "invalid",
            },
            context={"skip_validation": True},
        )


@pytest.mark.parametrize(
    "links,topics,playlists,expected",
    [
        pytest.param(
            "https://www.ted.com/talks/football",
            None,
            None,
            does_not_raise(),
            id="only-links-set",
        ),
        pytest.param(
            None,
            "football,soccer,sports",
            None,
            does_not_raise(),
            id="only-topics-set",
        ),
        pytest.param(
            None,
            None,
            "football,soccer,sports",
            does_not_raise(),
            id="only-playlists-set",
        ),
        pytest.param(None, None, None, pytest.raises(ValidationError), id="none-set"),
        pytest.param(
            "https://www.ted.com/talks/test",
            "science",
            None,
            pytest.raises(ValidationError),
            id="links-and-topics-set",
        ),
        pytest.param(
            "https://www.ted.com/talks/test",
            None,
            "playlist1",
            pytest.raises(ValidationError),
            id="links-and-playlists-set",
        ),
        pytest.param(
            None,
            "science",
            "playlist1",
            pytest.raises(ValidationError),
            id="topics-and-playlists-set",
        ),
        pytest.param(
            "https://www.ted.com/talks/test",
            "science",
            "playlist1",
            pytest.raises(ValidationError),
            id="links-topics-playlist-set",
        ),
    ],
)
def test_ted_flags_schema_fields_exclusivity(
    ted_flags_schema_cls: type[pydantic.BaseModel],
    links: str,
    topics: str,
    playlists: str,
    expected: RaisesContext[Exception],
):
    with expected:
        ted_flags_schema_cls(
            links=links,
            topics=topics,
            playlists=playlists,
            offliner_id="ted",
            name="ted-talks_mul_football",
        )


@pytest.mark.parametrize(
    "links,expected",
    [
        pytest.param(
            "https://www.ted.com/talks/football",
            does_not_raise(),
            id="valid-link",
        ),
        pytest.param(
            "https://www.ted.com/talks/football&",
            pytest.raises(ValidationError),
            id="invalid-link-with-ampersand",
        ),
        pytest.param(
            "https://www.ted.com/talks/football&,https://www.ted.com/talks/football",
            pytest.raises(ValidationError),
            id="invalid-link-with-valid-link",
        ),
        pytest.param(
            "https://www.ted.com/talks/test,https://www.ted.com/talks/test",
            does_not_raise(),
            id="multiple-valid-links",
        ),
    ],
)
def test_ted_flags_schema_links(
    ted_flags_schema_cls: type[pydantic.BaseModel],
    links: str,
    expected: RaisesContext[Exception],
):
    with expected:
        ted_flags_schema_cls(
            links=links,
            offliner_id="ted",
            name="ted-talks_mul_football",
        )


@pytest.mark.parametrize(
    "value,expected",
    [
        ("true", True),
        ("True", True),
        ("1", True),
        ("yes", True),
        ("y", True),
        ("Y", True),
        ("on", True),
        ("ON", True),
        ("false", False),
        ("FALSE", False),
        ("0", False),
        ("no", False),
        ("n", False),
        ("off", False),
        ("", False),
        ("anything_else", False),
        (True, True),
        (False, False),
        (1, True),
        (0, False),
        (None, False),
        ([], False),
        ({}, False),
    ],
)
def test_parse_bool(value: Any, *, expected: bool):
    """Test parse_bool function with various inputs."""
    assert parse_bool(value) == expected


@pytest.mark.parametrize(
    "value,expected",
    [
        pytest.param(True, does_not_raise(), id="true"),
        pytest.param(False, does_not_raise(), id="false"),
        pytest.param(
            "a random word",
            pytest.raises(ValidationError),
            id="string-true",
        ),
        pytest.param(
            "/output",
            pytest.raises(ValidationError),
            id="string-false",
        ),
        pytest.param(
            "",
            pytest.raises(ValidationError),
            id="empty-string",
        ),
    ],
)
def test_relaxed_boolean_model(
    *, value: str | int | bool, expected: RaisesContext[Exception]
):
    with expected:
        SkipableBoolModel.model_validate({"value": value})


@pytest.mark.parametrize(
    "value,expected",
    [
        pytest.param(True, does_not_raise(), id="true"),
        pytest.param(False, does_not_raise(), id="false"),
        pytest.param(
            "true",
            does_not_raise(),
            id="string-true",
        ),
        pytest.param(
            "false",
            does_not_raise(),
            id="string-false",
        ),
        pytest.param(
            0,
            does_not_raise(),
            id="integer-zero",
        ),
        pytest.param(
            1,
            does_not_raise(),
            id="integer-1",
        ),
        pytest.param(
            "",
            does_not_raise(),
            id="empty-string",
        ),
    ],
)
def test_relaxed_boolean_skip_validation(
    *, value: str | int | bool, expected: RaisesContext[Exception]
):
    with expected:
        SkipableBoolModel.model_validate(
            {"value": value}, context={"skip_validation": True}
        )


@pytest.mark.parametrize(
    "value,expected",
    [
        pytest.param("https://example.com", does_not_raise(), id="true"),
        pytest.param("a.b.cd", pytest.raises(ValidationError), id="invalid-url"),
        pytest.param(
            "https://example.com/path?query=value",
            does_not_raise(),
            id="valid-url-with-query",
        ),
        pytest.param(
            "./example.com",
            pytest.raises(ValidationError),
            id="invalid-url-with-relative-path",
        ),
        pytest.param(
            "//example.com",
            pytest.raises(ValidationError),
            id="invalid-url-with-protocol-relative-path",
        ),
    ],
)
def test_secret_url_model(value: str, expected: RaisesContext[Exception]):
    with expected:
        SecretUrlModel.model_validate({"value": value})


@pytest.mark.parametrize(
    "value,expected",
    [
        pytest.param("https://example.com", does_not_raise(), id="true"),
        pytest.param("a.b.cd", does_not_raise(), id="invalid-url"),
        pytest.param(
            "https://example.com/path?query=value",
            does_not_raise(),
            id="valid-url-with-query",
        ),
        pytest.param(
            "./example.com",
            does_not_raise(),
            id="invalid-url-with-relative-path",
        ),
        pytest.param(
            "//example.com",
            does_not_raise(),
            id="invalid-url-with-protocol-relative-path",
        ),
    ],
)
def test_secret_url_model_skip_validation(
    value: str, expected: RaisesContext[Exception]
):
    with expected:
        SecretUrlModel.model_validate(
            {"value": value}, context={"skip_validation": True}
        )


@pytest.mark.parametrize(
    "value,expected",
    [
        pytest.param("https://example.com", does_not_raise(), id="true"),
        pytest.param("a.b.cd", pytest.raises(ValidationError), id="invalid-url"),
        pytest.param(
            "https://example.com/path?query=value",
            does_not_raise(),
            id="valid-url-with-query",
        ),
        pytest.param(
            "./example.com",
            pytest.raises(ValidationError),
            id="invalid-url-with-relative-path",
        ),
        pytest.param(
            "//example.com",
            pytest.raises(ValidationError),
            id="invalid-url-with-protocol-relative-path",
        ),
    ],
)
def test_skipable_url_model(value: str, expected: RaisesContext[Exception]):
    with expected:
        SecretUrlModel.model_validate({"value": value})


@pytest.mark.parametrize(
    "value,expected",
    [
        pytest.param("https://example.com", does_not_raise(), id="true"),
        pytest.param("a.b.cd", does_not_raise(), id="invalid-url"),
        pytest.param(
            "https://example.com/path?query=value",
            does_not_raise(),
            id="valid-url-with-query",
        ),
        pytest.param(
            "./example.com",
            does_not_raise(),
            id="invalid-url-with-relative-path",
        ),
        pytest.param(
            "//example.com",
            does_not_raise(),
            id="invalid-url-with-protocol-relative-path",
        ),
    ],
)
def test_skipable_url_model_skip_validation(
    value: str, expected: RaisesContext[Exception]
):
    with expected:
        SecretUrlModel.model_validate(
            {"value": value}, context={"skip_validation": True}
        )


@pytest.mark.parametrize(
    "grapheme,skip_validation,expected",
    [
        pytest.param("é" * 30, False, does_not_raise()),
        pytest.param("é" * 40, False, pytest.raises(ValidationError)),
        pytest.param("é" * 40, True, does_not_raise()),
    ],
)
def test_grapheme_length_validation_on_strings(
    *, grapheme: str, skip_validation: bool, expected: RaisesContext[Exception]
):
    """Test that grapheme validation is applied to string flags."""
    field = generate_field_type(
        "mwoffliner",
        FlagSchema(
            type="string",
            label="ZIM Title",
            description="Custom ZIM title. Wiki name otherwise.",
            min_graphemes=1,
            max_graphemes=30,
        ),
        label="title",
    )
    model = create_model("mwofflinerFlagsSchema", __base__=CamelModel, title=field)
    with expected:
        model.model_validate(
            {"title": grapheme}, context={"skip_validation": skip_validation}
        )


@pytest.mark.parametrize(
    "grapheme,skip_validation,expected",
    [
        pytest.param(["é" * 30, "é" * 25], False, pytest.raises(ValidationError)),
        pytest.param(["é" * 40, "é" * 25], False, pytest.raises(ValidationError)),
        pytest.param(["é" * 40, "é" * 25], True, does_not_raise()),
    ],
)
def test_grapheme_length_validation_on_list_of_strings(
    *, grapheme: str, skip_validation: bool, expected: RaisesContext[Exception]
):
    """Test that grapheme validation is applied to the inner string in list of string flag"""
    field = generate_field_type(
        "mwoffliner",
        FlagSchema(
            type="string",
            label="ZIM Title",
            description="Custom ZIM title. Wiki name otherwise.",
            min_graphemes=1,
            max_graphemes=30,
        ),
        label="title",
    )
    model = create_model("mwofflinerFlagsSchema", __base__=CamelModel, title=field)
    with expected:
        model.model_validate(
            {"title": grapheme}, context={"skip_validation": skip_validation}
        )
