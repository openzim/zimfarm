from contextlib import nullcontext as does_not_raise
from typing import Any

import pytest
from _pytest.python_api import RaisesContext
from pydantic import ValidationError

from zimfarm_backend.common.constants import parse_bool
from zimfarm_backend.common.schemas.fields import (
    CommaSeparatedZIMLangCode,
    GraphemeStr,
    SecretUrl,
    SkipableBool,
    SkipableUrl,
    ZIMFileName,
    ZIMLangCode,
    ZIMName,
    ZIMTitle,
)
from zimfarm_backend.common.schemas.models import BaseModel
from zimfarm_backend.common.schemas.offliners import TedFlagsSchema
from zimfarm_backend.common.schemas.offliners.freecodecamp import (
    FCCLanguageValue,
)


class FCCLanguageModel(BaseModel):
    value: FCCLanguageValue


class ZIMFileNameModel(BaseModel):
    value: ZIMFileName


class ZIMNameModel(BaseModel):
    value: ZIMName


class ZIMLanguageCodeModel(BaseModel):
    value: ZIMLangCode


class ZIMTitleModel(BaseModel):
    value: ZIMTitle


class CommaSeparatedZIMLanguageCodeModel(BaseModel):
    value: CommaSeparatedZIMLangCode


class SkipableBoolModel(BaseModel):
    value: SkipableBool


class SecretUrlModel(BaseModel):
    value: SecretUrl


class SkipableUrlModel(BaseModel):
    value: SkipableUrl


def test_enum_validator_accepts_valid_value():
    with does_not_raise():
        FCCLanguageModel.model_validate({"value": "eng"})


def test_enum_validator_rejects_invalid_value():
    with pytest.raises(ValidationError):
        FCCLanguageModel.model_validate({"value": "jp"})


def test_enum_validator_skips_validation_when_context_set():
    with does_not_raise():
        FCCLanguageModel.model_validate(
            {"value": "invalid"}, context={"skip_validation": True}
        )


@pytest.mark.parametrize(
    "filename,expected",
    [
        ("wikipedia_en_all_2024-01.zim", does_not_raise()),
        ("ted-talks_eng_all_2024-03.zim", does_not_raise()),
        ("wikipedia_eng_all_{period}.zim", does_not_raise()),
        ("ted-talks_eng_football_{period}.zim", does_not_raise()),
        ("wikipedia_en_all_nopic_2024-01.zim", does_not_raise()),  # selection + flavor
        # Invalid filenames
        (
            "wikipedia_eng_all_2024-01",
            pytest.raises(ValidationError),
        ),  # Missing .zim extension
        (
            "WIKIPEDIA_EN_ALL_2024-01.zim",
            pytest.raises(ValidationError),
        ),  # Uppercase letters
        (
            "wikipedia_eng_all_2024_01.zim",
            pytest.raises(ValidationError),
        ),  # Wrong date format (underscore instead of dash)
        ("_en_all_2024-01.zim", pytest.raises(ValidationError)),  # Empty first part
        (
            "wikipedia__all_2024-01.zim",
            pytest.raises(ValidationError),
        ),  # Empty language part
        ("wikipedia_en_all_.zim", pytest.raises(ValidationError)),  # Empty date part
        (
            "wikipedia_en_all_2024-01_.zim",
            pytest.raises(ValidationError),
        ),  # Trailing underscore after period
        (
            "_wikipedia_en_all_2024-01.zim",
            pytest.raises(ValidationError),
        ),  # Leading underscore
        (
            "wikipedia en_all_2024-01.zim",
            pytest.raises(ValidationError),
        ),  # Space in first part
        (
            "wikipedia_en_all 2024-01.zim",
            pytest.raises(ValidationError),
        ),  # Space in date part
    ],
)
def test_zimfilename_pattern(filename: str, expected: RaisesContext[Exception]):
    """Test ZIMFileName pattern validation with various inputs."""
    with expected:
        ZIMFileNameModel.model_validate({"value": filename})


def test_zimfilename_skips_validation_when_context_set():
    """Test that ZIMFileName validation is skipped when context is set."""
    with does_not_raise():
        ZIMFileNameModel.model_validate(
            {"value": "invalid_filename"}, context={"skip_validation": True}
        )


@pytest.mark.parametrize(
    "name,expected",
    [
        # Zim name is made of three parts {domain}_{lang}_{selection} with _ as
        # the separator
        # Valid ZIM names
        pytest.param(
            "android.stackexchange.com_eng_all",
            does_not_raise(),
            id="first_part_domain_name",
        ),
        pytest.param(
            "ted-talks_eng_football", does_not_raise(), id="hypen_in_first_part"
        ),
        pytest.param(
            "wikipedia_nds-nl_top", does_not_raise(), id="hypen_in_second_part"
        ),
        # Invalid ZIM names
        pytest.param(
            "wikipedia_en_all_2024-01", pytest.raises(ValidationError), id="four_parts"
        ),  # Too many parts (4 instead of 3)
        pytest.param(
            "wikipedia_en", pytest.raises(ValidationError), id="two_parts"
        ),  # Too few parts (2 instead of 3)
        pytest.param(
            "WIKIPEDIA_EN_ALL", pytest.raises(ValidationError), id="upper_case_letters"
        ),  # Uppercase letters
        pytest.param(
            "wikipedia EN all",
            pytest.raises(ValidationError),
            id="space_separator",
        ),  # Spaces instead of underscores
        pytest.param(
            "wikipedia_en_all_",
            pytest.raises(ValidationError),
            id="trailing_underscore",
        ),  # Trailing underscore
        pytest.param(
            "_wikipedia_en_all",
            pytest.raises(ValidationError),
            id="leading_underscore",
        ),  # Leading underscore
        pytest.param(
            "wikipedia__all", pytest.raises(ValidationError), id="missing_middle_part"
        ),  # Empty middle part
        pytest.param(
            "wikipedia_en_", pytest.raises(ValidationError), id="empty_last_part"
        ),  # Empty last part
        pytest.param(
            "_en_all",
            pytest.raises(ValidationError),
        ),  # Empty first part
        pytest.param(
            "wikipedia_en_all.zim",
            does_not_raise(),
            id="file_extension_in_name",
        ),  # File extension not allowed (not sure yet??)
        pytest.param(
            "wikipedia@en_all", pytest.raises(ValidationError), id="special_char_at"
        ),  # Special character @
        pytest.param(
            "wikipedia&en_all",
            pytest.raises(ValidationError),
            id="special_char_ampersand",
        ),  # Special character &
        pytest.param(
            "wikipedia*en_all",
            pytest.raises(ValidationError),
            id="special_char_astersik",
        ),  # Special character *
        pytest.param(
            "", pytest.raises(ValidationError), id="empty_string"
        ),  # Empty string
    ],
)
def test_zimname_pattern(name: str, expected: RaisesContext[Exception]):
    """Test ZIMName pattern validation with various inputs."""
    with expected:
        ZIMNameModel.model_validate({"value": name})


def test_zimname_skips_validation_when_context_set():
    """Test that ZIMName validation is skipped when context is set."""
    with does_not_raise():
        ZIMNameModel.model_validate(
            {"value": "invalid_name"}, context={"skip_validation": True}
        )


@pytest.mark.parametrize(
    "language_code,expected",
    [
        ("eng", does_not_raise()),
        ("fra", does_not_raise()),
        ("jpn", does_not_raise()),
        ("jp", pytest.raises(ValidationError)),
        ("en", pytest.raises(ValidationError)),
        ("invalid", pytest.raises(ValidationError)),
    ],
)
def test_language_code_validator(
    language_code: str, expected: RaisesContext[Exception]
):
    """Test language code validator with various inputs."""
    with expected:
        ZIMLanguageCodeModel.model_validate({"value": language_code})


def test_language_code_validator_skips_validation_when_context_set():
    """Test that language code validator is skipped when context is set."""
    with does_not_raise():
        ZIMLanguageCodeModel.model_validate(
            {"value": "invalid"}, context={"skip_validation": True}
        )


@pytest.mark.parametrize(
    "languages,expected",
    [
        pytest.param("eng,fra,jpn", does_not_raise(), id="valid_languages"),
        pytest.param(
            "en,fr,jp", pytest.raises(ValidationError), id="invalid_language_code"
        ),
    ],
)
def test_ted_flags_schema(languages: str, expected: RaisesContext[Exception]):
    with expected:
        TedFlagsSchema(
            name="ted-talks_mul_football",
            offliner_id="ted",
            languages=languages,
            topics="football",
        )


def test_ted_flags_schema_skips_validation_when_context_set():
    with does_not_raise():
        TedFlagsSchema.model_validate(
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
    links: str, topics: str, playlists: str, expected: RaisesContext[Exception]
):
    with expected:
        TedFlagsSchema(
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
def test_ted_flags_schema_links(links: str, expected: RaisesContext[Exception]):
    with expected:
        TedFlagsSchema(
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
    "string,expected_length",
    [
        ("hello", 5),
        ("世界", 2),
        ("🌍", 1),
        ("👨‍👩‍👧‍👦", 1),
        ("👨‍👩‍👧‍👦👨‍👩‍👧‍👦", 2),
        ("👨‍👩‍👧‍👦👨‍👩‍👧‍👦👨‍👩‍👧‍👦", 3),
    ],
)
def test_grapheme_str(string: str, expected_length: int):
    assert len(GraphemeStr(string)) == expected_length


@pytest.mark.parametrize(
    "string,expected",
    [
        ("hello", does_not_raise()),
        ("世界", does_not_raise()),
        ("🌍" * 30, does_not_raise()),
        ("👨‍👩‍👧‍👦" * 30, does_not_raise()),
        ("👨‍👩‍👧‍👦👨‍👩‍👧‍👦👨‍👩‍👧‍👦", does_not_raise()),
        # Test strings longer than 30 characters that should fail
        ("This is a very long title that should fail", pytest.raises(ValidationError)),
        ("ThisIsALongTitleWithoutSpacesThatShouldFail", pytest.raises(ValidationError)),
        ("A string with exactly 31 characters!", pytest.raises(ValidationError)),
        (
            "Another string that is way too long to be a valid ZIM title",
            pytest.raises(ValidationError),
        ),
        ("👨‍👩‍👧‍👦" * 31, pytest.raises(ValidationError)),  # Long string of emojis
        (
            "世界" * 20,
            pytest.raises(ValidationError),
        ),  # Long string of Chinese characters
    ],
)
def test_zimtitle_string(string: str, expected: RaisesContext[Exception]):
    with expected:
        ZIMTitleModel.model_validate({"value": string})


@pytest.mark.parametrize(
    "string",
    [
        ("hello"),
        ("世界"),
        ("🌍"),
        ("👨‍👩‍👧‍👦"),
        ("👨‍👩‍👧‍👦👨‍👩‍👧‍👦👨‍👩‍👧‍👦"),
        ("This is a very long title that should fail"),
        ("ThisIsALongTitleWithoutSpacesThatShouldFail"),
        ("A string with exactly 31 characters!"),
        ("Another string that is way too long to be a valid ZIM title",),
        ("👨‍👩‍👧‍👦" * 31),
        ("世界" * 20,),
    ],
)
def test_zimtitle_string_does_not_raise(string: str):
    with does_not_raise():
        ZIMTitleModel.model_validate(
            {"value": string}, context={"skip_validation": True}
        )


@pytest.mark.parametrize(
    "languages,expected",
    [
        pytest.param("eng", does_not_raise(), id="single-valid-language-code"),
        pytest.param("eng,fra,jpn", does_not_raise(), id="multiple-valid-languages"),
        pytest.param(
            "en,fr,jp",
            pytest.raises(ValidationError),
            id="multiple-invalid-language-codes",
        ),
        pytest.param(
            "en",
            pytest.raises(ValidationError),
            id="single-invalid-language-code",
        ),
        pytest.param(
            "eng,",
            pytest.raises(ValidationError),
            id="valid-language-code-with-trailing-comma",
        ),
        pytest.param(
            "eng,,",
            pytest.raises(ValidationError),
            id="valid-language-code-with-double-trailing-comma",
        ),
        pytest.param(
            "eng,fr,jpn",
            pytest.raises(ValidationError),
            id="multiple-valid-languages-with-one-invalid",
        ),
    ],
)
def test_comma_separated_zim_language_code_validator(
    languages: str, expected: RaisesContext[Exception]
):
    with expected:
        CommaSeparatedZIMLanguageCodeModel.model_validate({"value": languages})


@pytest.mark.parametrize(
    "languages,expected",
    [
        pytest.param("eng", does_not_raise(), id="single-valid-language-code"),
        pytest.param("eng,fra,jpn", does_not_raise(), id="multiple-valid-languages"),
        pytest.param(
            "en,fr,jp", does_not_raise(), id="multiple-invalid-language-codes"
        ),
        pytest.param("en", does_not_raise(), id="single-invalid-language-code"),
        pytest.param(
            "eng,", does_not_raise(), id="valid-language-code-with-trailing-comma"
        ),
        pytest.param(
            "eng,,",
            does_not_raise(),
            id="valid-language-code-with-double-trailing-comma",
        ),
        pytest.param(
            "eng,fr,jpn",
            does_not_raise(),
            id="multiple-valid-languages-with-one-invalid",
        ),
    ],
)
def test_comma_separated_zim_language_code_validator_skips_validation_when_context_set(
    languages: str, expected: RaisesContext[Exception]
):
    with expected:
        CommaSeparatedZIMLanguageCodeModel.model_validate(
            {"value": languages}, context={"skip_validation": True}
        )


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
    value: str | int | bool, expected: RaisesContext[Exception]
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
    value: str | int | bool, expected: RaisesContext[Exception]
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
