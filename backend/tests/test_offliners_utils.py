from typing import Any

import pytest

from zimfarm_backend.utils.offliners import compute_flags, simplified


@pytest.mark.parametrize(
    "value,expected",
    [
        pytest.param(123, "123", id="integer"),
        pytest.param(123.0, "123", id="float_integer"),
        pytest.param(123.5, "123.5", id="float_decimal"),
        pytest.param("hello", "hello", id="string"),
        pytest.param("", "", id="empty_string"),
        pytest.param(True, "True", id="boolean_true"),
        pytest.param(False, "False", id="boolean_false"),
        pytest.param(0, "0", id="zero_integer"),
        pytest.param(0.0, "0", id="zero_float"),
    ],
)
def test_simplified(value: Any, expected: str) -> None:
    """Test the simplified function for various input types."""
    assert simplified(value) == expected


@pytest.mark.parametrize(
    "flags,use_equals,expected",
    [
        # Basic boolean flags
        pytest.param(
            {"verbose": True, "quiet": False, "debug": None},
            True,
            ["--verbose"],
            id="boolean_flags_with_equals",
        ),
        pytest.param(
            {"verbose": True, "quiet": False, "debug": None},
            False,
            ["--verbose"],
            id="boolean_flags_without_equals",
        ),
        # String values with equals
        pytest.param(
            {"title": "My Title", "description": "My Description"},
            True,
            ["--title='My Title'", "--description='My Description'"],
            id="string_values_with_equals",
        ),
        # String values without equals
        pytest.param(
            {"title": "My Title", "description": "My Description"},
            False,
            ["--title", "'My Title'", "--description", "'My Description'"],
            id="string_values_without_equals",
        ),
        # List values
        pytest.param(
            {"tags": ["tag1", "tag2"], "categories": ["cat1"]},
            True,
            ["--tags=tag1", "--tags=tag2", "--categories=cat1"],
            id="list_values_with_equals",
        ),
        pytest.param(
            {"tags": ["tag1", "tag2"], "categories": ["cat1"]},
            False,
            ["--tags", "tag1", "--tags", "tag2", "--categories", "cat1"],
            id="list_values_without_equals",
        ),
    ],
)
def test_compute_flags_basic(
    *,
    flags: dict[str, str | bool | list[str] | None],
    use_equals: bool,
    expected: list[str],
) -> None:
    """Test compute_flags with basic input types."""
    result = compute_flags(flags, use_equals=use_equals)
    assert result == expected


@pytest.mark.parametrize(
    "flags,use_equals,expected",
    [
        pytest.param(
            {
                "description": """אנצקלופדיה חב"דית המקיפה את כלל מושגי ואישי חסידות חב"ד"""  # noqa: E501
            },
            False,
            [
                "--description",
                "'אנצקלופדיה חב\"דית המקיפה את כלל מושגי ואישי חסידות חב\"ד'",
            ],
            id="hebrew_text_without_equals",
        ),
        # Text with quotes
        pytest.param(
            {"title": 'Title with "quotes"'},
            True,
            ["--title='Title with \"quotes\"'"],
            id="double_quotes_with_equals",
        ),
        # Text with special characters
        pytest.param(
            {"description": "Text with $variables & symbols"},
            True,
            ["--description='Text with $variables & symbols'"],
            id="special_characters_with_equals",
        ),
        pytest.param(
            {"description": "Text with spaces and\ttabs"},
            True,
            ["--description='Text with spaces and\ttabs'"],
            id="tabs_with_equals",
        ),
        # Text with newlines
        pytest.param(
            {"description": "Line 1\nLine 2"},
            True,
            ["--description='Line 1\nLine 2'"],
            id="newlines_with_equals",
        ),
    ],
)
def test_compute_flags_special_characters(
    *,
    flags: dict[str, str | bool | list[str] | None],
    use_equals: bool,
    expected: list[str],
) -> None:
    """Test compute_flags with special characters and shell-sensitive content."""
    result = compute_flags(flags, use_equals=use_equals)
    assert result == expected


@pytest.mark.parametrize(
    "flags,expected",
    [
        # Test that offliner_id variants are filtered out
        pytest.param(
            {
                "offliner_id": "test",
                "offlinerId": "test",
                "offliner-id": "test",
                "title": "My Title",
            },
            ["--title='My Title'"],
            id="filter_offliner_id_variants",
        ),
        # Test with other flags
        pytest.param(
            {
                "offliner_id": "test",
                "verbose": True,
                "title": "My Title",
                "count": 5,
            },
            ["--verbose", "--title='My Title'", "--count=5"],
            id="filter_offliner_id_with_other_flags",
        ),
    ],
)
def test_compute_flags_filters_offliner_id(
    flags: dict[str, str | bool | list[str] | None], expected: list[str]
) -> None:
    """Test that offliner_id variants are properly filtered out."""
    result = compute_flags(flags, use_equals=True)
    assert result == expected
