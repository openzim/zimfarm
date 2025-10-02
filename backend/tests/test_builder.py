from contextlib import nullcontext as does_not_raise

import pytest
from _pytest.python_api import RaisesContext

from zimfarm_backend.common.schemas.offliners.builder import (
    get_base_model_cls,
    get_field_validator,
    get_model_validator,
)


@pytest.mark.parametrize(
    "validator_name,exception",
    [
        ("check_exclusive_fields", does_not_raise()),
        ("invalid_validator", pytest.raises(ValueError)),
    ],
)
def test_get_model_validator(validator_name: str, exception: RaisesContext[Exception]):
    with exception:
        get_model_validator(validator_name)


@pytest.mark.parametrize(
    "validator_name,exception",
    [
        ("validate_ted_links", does_not_raise()),
        ("language_code", does_not_raise()),
        ("invalid_validator", pytest.raises(ValueError)),
    ],
)
def test_get_field_validator(validator_name: str, exception: RaisesContext[Exception]):
    with exception:
        get_field_validator(validator_name)


@pytest.mark.parametrize(
    "model_name,exception",
    [
        ("DashModel", does_not_raise()),
        ("CamelModel", does_not_raise()),
        ("BaseModel", pytest.raises(ValueError)),
    ],
)
def test_get_base_model_cls(model_name: str, exception: RaisesContext[Exception]):
    with exception:
        get_base_model_cls(model_name)
