from contextlib import nullcontext as does_not_raise

import pytest
from pydantic import ValidationError

from zimfarm_backend.common.schemas.models import BaseModel
from zimfarm_backend.common.schemas.offliners.freecodecamp import (
    FCCLanguageValue,
)


class TestModel(BaseModel):
    value: FCCLanguageValue


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
