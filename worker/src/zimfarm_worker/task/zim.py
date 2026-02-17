from __future__ import annotations

import base64
import io
import pathlib
from typing import Any, NamedTuple

from libzim.reader import Archive  # pyright: ignore[reportMissingModuleSource]


def get_zim_info(fpath: pathlib.Path) -> dict[str, Any]:
    zim = Archive(fpath)
    payload: dict[str, Any] = {
        "id": str(zim.uuid),
        "counter": counters(zim),
        "article_count": zim.article_count,
        "media_count": zim.media_count,
        "size": fpath.stat().st_size,
        "metadata": {
            key: get_text_metadata(zim, key)
            for key in zim.metadata_keys
            if not key.startswith("Illustration_")
        },
    }
    for size in zim.get_illustration_sizes():
        payload["metadata"].update(
            {
                f"Illustration_{size}x{size}@1": base64.standard_b64encode(
                    zim.get_illustration_item(size).content
                ).decode("ASCII")
            }
        )
    return payload


# Code below is duplicated from python-scraperlib, in order to depend only on
# python-libzim in the task manager, and not the whole python-scraperlib and all its
# dependencies


class MimetypeAndCounter(NamedTuple):
    mimetype: str
    value: int


CounterMap = dict[str, int]


def get_text_metadata(zim: Archive, name: str) -> str:
    """Decoded value of a text metadata"""
    return zim.get_metadata(name).decode("UTF-8")


def getline(src: io.StringIO, delim: str | None = None) -> tuple[bool, str]:
    """C++ stdlib getline() ~clone

    Reads `src` until it finds `delim`.
    returns whether src is EOF and the extracted string (delim excluded)"""
    output = ""
    if not delim:
        return True, src.read()

    char = src.read(1)
    while char:
        if char == delim:
            break
        output += char
        char = src.read(1)
    return char == "", output


def counters(zim: Archive) -> dict[str, int]:
    try:
        return parse_mimetype_counter(get_text_metadata(zim, "Counter"))
    except RuntimeError:  # pragma: no cover (no ZIM avail to test itl)
        return {}  # pragma: no cover


def read_full_mimetype_and_counter_string(
    src: io.StringIO,
) -> tuple[bool, str]:
    """read a single mimetype-and-counter string from source

    Returns whether the source is EOF and the extracted string (or empty one)"""
    params = ""
    eof, mtc_str = getline(src, ";")  # pyright: ignore
    if mtc_str.find("=") == -1:
        while params.count("=") != 2:  # noqa: PLR2004
            eof, params = getline(src, ";")  # pyright: ignore
            if params.count("=") == 2:  # noqa: PLR2004
                mtc_str += ";" + params
            if eof:
                break
    return eof, mtc_str


def parse_a_single_mimetype_counter(string: str) -> MimetypeAndCounter:
    """MimetypeAndCounter from a single mimetype-and-counter string"""
    k: int = string.rfind("=")
    if k != len(string) - 1:
        mime_type: str = string[:k]
        counter: str = string[k + 1 :]
        try:
            return MimetypeAndCounter(mime_type, int(counter))
        except ValueError:
            pass  # value is not castable to int
    return MimetypeAndCounter("", 0)


def parse_mimetype_counter(
    counter_data: str,
) -> CounterMap:
    """Mapping of MIME types with count for each from ZIM Counter metadata string"""
    counters: CounterMap = {}
    ss = io.StringIO(counter_data)
    eof = False
    while not eof:
        eof, mtc_str = read_full_mimetype_and_counter_string(ss)
        mtc = parse_a_single_mimetype_counter(mtc_str)
        if mtc.mimetype:
            counters.update([mtc])
    ss.close()
    return counters
