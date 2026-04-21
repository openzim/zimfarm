import hashlib
from collections.abc import Callable
from functools import partial
from itertools import chain
from urllib.parse import urlparse

from humanfriendly import format_size

from zimfarm_backend.common.constants import BLOB_MAX_SIZE
from zimfarm_backend.common.schemas.offliners.models import (
    PreparedBlob,
    TransformerSchema,
)


def get_transformer_function(
    transformer: TransformerSchema,
) -> Callable[[str], list[str]]:
    def _get_hostname(url: str) -> list[str]:
        if not url.startswith(("https://", "http://")):
            url = "https://" + url
        return [urlparse(url).hostname or ""]

    match transformer.name:
        case "split":
            return partial(str.split, sep=transformer.operand)
        case "hostname":
            return _get_hostname
        case None:
            # return the value as it is if there is no transformer associated
            return lambda x: [x]
        case _:  # pyright: ignore[reportUnnecessaryComparison]
            raise ValueError(
                f"No transformer function registered for '{transformer.name}'"
            )


def transform_data(data: list[str], transformers: list[TransformerSchema]) -> list[str]:
    """Generate the output by applying each tranformer to data"""
    if not transformers:
        return data
    head, *tail = transformers
    return transform_data(
        list(
            chain.from_iterable(
                # apply the transformer function to each entry in the list
                # and feed the new list as input to the next transformer function
                [
                    get_transformer_function(head)(entry)
                    for entry in data
                    if entry.strip()
                ]
            )
        ),
        tail,
    )


def prepare_blob(*, blob_data: bytes, kind: str, flag_name: str) -> PreparedBlob:
    """Prepare blob fields for upload"""

    if len(blob_data) > BLOB_MAX_SIZE:
        raise ValueError(
            f"Blob size ({format_size(len(blob_data), binary=True)} bytes) "
            "exceeds maximum allowed size "
            f"({format_size(BLOB_MAX_SIZE, binary=True)})"
        )

    return PreparedBlob(
        kind=kind,
        flag_name=flag_name,
        checksum=hashlib.sha256(blob_data).hexdigest(),
        data=blob_data,
    )


def get_extension_from_kind(kind: str) -> str:
    """Simple extension mapping from kind"""
    if kind == "css":
        return ".css"
    elif kind in ("image", "illustration"):
        return ".png"
    elif kind == "html":
        return ".html"
    elif kind == "txt":
        return ".txt"
    return ".bin"
