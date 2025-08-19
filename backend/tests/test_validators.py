from contextlib import nullcontext as does_not_raise

import pytest
from _pytest.python_api import RaisesContext
from pydantic import ValidationError

from zimfarm_backend.common.schemas.fields import ZIMFileName
from zimfarm_backend.common.schemas.models import BaseModel
from zimfarm_backend.common.schemas.offliners.freecodecamp import (
    FCCLanguageValue,
)


class TestModel(BaseModel):
    value: FCCLanguageValue


class TestZIMFileNameModel(BaseModel):
    value: ZIMFileName


def test_enum_validator_accepts_valid_value():
    with does_not_raise():
        TestModel.model_validate({"value": "eng"})


def test_enum_validator_rejects_invalid_value():
    with pytest.raises(ValidationError):
        TestModel.model_validate({"value": "jp"})


def test_enum_validator_skips_validation_when_context_set():
    with does_not_raise():
        TestModel.model_validate(
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
        TestZIMFileNameModel.model_validate({"value": filename})


def test_zimfilename_skips_validation_when_context_set():
    """Test that ZIMFileName validation is skipped when context is set."""
    with does_not_raise():
        TestZIMFileNameModel.model_validate(
            {"value": "invalid_filename"}, context={"skip_validation": True}
        )
