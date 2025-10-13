import pytest

from zimfarm_backend.common.schemas.offliners.models import TransformerSchema
from zimfarm_backend.common.schemas.offliners.transformers import transform_data


@pytest.mark.parametrize(
    "transformers,data,expected",
    [
        pytest.param(
            [TransformerSchema(name="split", operator=",")],
            ["a,b,c"],
            ["a", "b", "c"],
            id="split-operator-only",
        ),
        pytest.param(
            [TransformerSchema(name="hostname")],
            ["https://example.com"],
            ["example.com"],
            id="hostname-only",
        ),
        pytest.param(
            [
                TransformerSchema(name="split", operator=","),
                TransformerSchema(name="hostname"),
            ],
            ["https://example.com,https://example.org"],
            ["example.com", "example.org"],
            id="split-first-then-hostname",
        ),
        pytest.param(
            [
                TransformerSchema(name="hostname"),
                TransformerSchema(name="split", operator=","),
            ],
            ["https://example.com,https://example.org"],
            # hostname first returns example.com,https
            ["example.com", "https"],
            id="hostname-first-then-split",
        ),
    ],
)
def test_transform_data(
    transformers: list[TransformerSchema], data: list[str], expected: list[str]
):
    assert transform_data(data, transformers) == expected
