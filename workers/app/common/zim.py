import base64
import pathlib
from typing import Any, Dict

from zimscraperlib.zim import Archive


def get_zim_info(fpath: pathlib.Path) -> Dict[str, Any]:
    zim = Archive(fpath)
    payload = {
        "id": str(zim.uuid),
        "counter": zim.counters,
        "article_count": zim.article_counter,
        "media_count": zim.media_counter,
        "size": fpath.stat().st_size,
        "metadata": zim.metadata,
    }
    for size in zim.get_illustration_sizes():
        payload["metadata"].update(
            {
                f"Illustration_{size}x{size}": base64.standard_b64encode(
                    zim.get_illustration_item(size).content
                ).decode("ASCII")
            }
        )
    return payload
