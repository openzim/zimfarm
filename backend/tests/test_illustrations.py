import io
from pathlib import Path

import pytest
from PIL.Image import open as pilopen

from zimfarm_backend.api.constants import ZIM_ILLUSTRATION_SIZE
from zimfarm_backend.api.image import create_zim_illustration

COMMONS_IMAGE_PATH = (Path(__file__).parent / "files/commons.png").resolve()
COMMONS_48_IMAGE_PATH = (Path(__file__).parent / "files/commons48.png").resolve()


@pytest.mark.parametrize(
    "user_illustration",
    [
        pytest.param(COMMONS_IMAGE_PATH, id="big_commons"),
        pytest.param(COMMONS_48_IMAGE_PATH, id="small_commons"),
    ],
)
def test_get_zim_illustration(
    user_illustration: Path,
):
    image = io.BytesIO(create_zim_illustration(user_illustration.read_bytes()))
    with pilopen(image) as image_details:
        assert image_details.format == "PNG"
        assert image_details.size == (ZIM_ILLUSTRATION_SIZE, ZIM_ILLUSTRATION_SIZE)
