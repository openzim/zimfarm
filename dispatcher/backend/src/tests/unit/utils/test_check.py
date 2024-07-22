import pytest

from utils.check import cleanup_value


@pytest.mark.parametrize(
    "value, expected",
    [
        pytest.param("ok", "ok", id="str_simple_ok"),
        pytest.param("o\u0000k", "ok", id="str_null_character"),
        pytest.param(123, 123, id="int_simple"),
    ],
)
def test_cleanup_value(value: str, expected: str):
    assert cleanup_value(value) == expected
