import hashlib
import uuid
from collections.abc import Callable
from functools import partial
from itertools import chain
from urllib.parse import urlparse

import requests
from humanfriendly import format_size
from pydantic import AnyUrl

from zimfarm_backend.common.constants import (
    BLOB_MAX_SIZE,
    BLOB_PRIVATE_STORAGE_URL,
    BLOB_PUBLIC_STORAGE_URL,
    BLOB_STORAGE_PASSWORD,
    BLOB_STORAGE_USERNAME,
    REQUESTS_TIMEOUT,
)
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

    filename = generate_blob_name_uuid(kind)
    return PreparedBlob(
        kind=kind,
        private_url=AnyUrl(f"{BLOB_PRIVATE_STORAGE_URL}/{filename}"),
        url=AnyUrl(f"{BLOB_PUBLIC_STORAGE_URL}/{filename}"),
        flag_name=flag_name,
        checksum=hashlib.sha256(blob_data).hexdigest(),
        data=blob_data,
    )


def generate_blob_name_uuid(
    kind: str,
) -> str:
    """
    Generate random UUID-based filename.
    """
    blob_uuid = uuid.uuid4()
    extension = get_extension_from_kind(kind)
    return f"{blob_uuid}{extension}"


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


def upload_blob(request: PreparedBlob):
    """
    Upload blob data to upstream storage.
    """
    headers = {
        "Content-Type": "application/octet-stream",
    }
    response = requests.put(
        str(request.private_url),
        headers=headers,
        data=request.data,
        timeout=REQUESTS_TIMEOUT,
        auth=(BLOB_STORAGE_USERNAME, BLOB_STORAGE_PASSWORD),
    )
    response.raise_for_status()
