import io
import tempfile
from pathlib import Path

from zimscraperlib.image import convert_image
from zimscraperlib.image.illustration import get_zim_illustration

from zimfarm_backend.api.constants import ZIM_ILLUSTRATION_SIZE


def convert_image_to_png(image: bytes) -> bytes:
    """Convert an image to PNG"""
    src = io.BytesIO(image)
    dst = io.BytesIO()
    convert_image(src, dst, fmt="PNG")
    dst.seek(0)
    return dst.read()


def create_zim_illustration(value: bytes) -> bytes:
    """Create an illustration image for ZIM files"""
    with tempfile.NamedTemporaryFile() as fp:
        fp.write(value)
        fp.flush()
        dst = get_zim_illustration(
            Path(fp.name), width=ZIM_ILLUSTRATION_SIZE, height=ZIM_ILLUSTRATION_SIZE
        )
        dst.seek(0)
        return dst.read()
