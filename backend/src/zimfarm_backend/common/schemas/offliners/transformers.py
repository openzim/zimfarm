from collections.abc import Callable
from functools import partial
from itertools import chain
from urllib.parse import urlparse

from zimfarm_backend.common.schemas.offliners.models import TransformerSchema


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
        case _:
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
