import base64
import hashlib
import uuid
from collections.abc import Callable
from functools import partial
from itertools import chain
from typing import NamedTuple
from urllib.parse import urlparse

import requests
from humanfriendly import format_size
from pydantic import AnyUrl, BaseModel

from zimfarm_backend.common.constants import (
    BLOB_MAX_SIZE,
    BLOB_STORAGE_PASSWORD,
    BLOB_STORAGE_URL,
    BLOB_STORAGE_USERNAME,
    REQUESTS_TIMEOUT,
)
from zimfarm_backend.common.schemas.offliners.models import (
    OfflinerSpecSchema,
    ProcessedBlob,
    TransformerSchema,
)


class UploadResponse(NamedTuple):
    url: str
    checksum: str


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


def process_blob_fields(
    data: BaseModel,
    schema: OfflinerSpecSchema,
) -> list[ProcessedBlob]:
    """Upload blob data and update flag with URL if needed, or keep URLs as is."""

    results: list[ProcessedBlob] = []
    for flag_name, flag_schema in schema.flags.items():
        if flag_schema.type != "blob":
            continue

        value = getattr(data, flag_name)

        if value and not value.startswith("http"):
            if flag_schema.kind is None:
                raise ValueError("Blobs must have a 'kind'")

            response = upload_blob(data=value, kind=flag_schema.kind)
            setattr(data, flag_name, response.url)
            results.append(
                ProcessedBlob(
                    kind=flag_schema.kind,
                    url=AnyUrl(response.url),
                    flag_name=flag_name,
                    checksum=response.checksum,
                )
            )
    return results


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
    elif kind == "image":
        return ".png"
    return ".bin"


def upload_blob(*, data: str, kind: str) -> UploadResponse:
    """
    Upload blob data to upstream storage and return the URL.
    """
    # Extract base64 data if it's a data URI
    if data.startswith("data:"):
        _, encoded_data = data.split(",", 1)
    else:
        encoded_data = data

    blob_data = base64.b64decode(encoded_data)

    if len(blob_data) > BLOB_MAX_SIZE:
        raise ValueError(
            f"Blob size ({format_size(len(blob_data), binary=True)} bytes) exceeds "
            f"maximum allowed size ({format_size(BLOB_MAX_SIZE, binary=True)})"
        )

    checksum = hashlib.sha256(blob_data).hexdigest()

    headers = {
        "Content-Type": "application/octet-stream",
    }
    filename = generate_blob_name_uuid(kind)

    url = f"{BLOB_STORAGE_URL}/{filename}"
    response = requests.put(
        url,
        headers=headers,
        data=blob_data,
        timeout=REQUESTS_TIMEOUT,
        auth=(BLOB_STORAGE_USERNAME, BLOB_STORAGE_PASSWORD),
    )
    response.raise_for_status()
    return UploadResponse(checksum=checksum, url=url)
