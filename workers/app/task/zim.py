from __future__ import annotations

import base64
import io
import pathlib
from collections import namedtuple
from typing import Any, Dict, Optional

from libzim import Archive


def get_zim_info(fpath: pathlib.Path) -> Dict[str, Any]:
    zim = Archive(fpath)
    payload = {
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
                f"Illustration_{size}x{size}": base64.standard_b64encode(
                    zim.get_illustration_item(size).content
                ).decode("ASCII")
            }
        )
    return payload


# Code below is duplicated from python-scraperlib, in order to depend only on
# python-libzim in the task manager, and not the whole python-scraperlib and all its
# dependencies

MimetypeAndCounter = namedtuple("MimetypeAndCounter", ["mimetype", "value"])
CounterMap = Dict[
    type(MimetypeAndCounter.mimetype), type(MimetypeAndCounter.value)  # pyright: ignore
]


def get_text_metadata(zim: Archive, name: str) -> str:
    """Decoded value of a text metadata"""
    return zim.get_metadata(name).decode("UTF-8")


def getline(src: io.StringIO, delim: Optional[bool] = None) -> tuple[bool, str]:
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
        return parseMimetypeCounter(get_text_metadata(zim, "Counter"))
    except RuntimeError:  # pragma: no cover (no ZIM avail to test itl)
        return {}  # pragma: no cover


def readFullMimetypeAndCounterString(
    src: io.StringIO,
) -> tuple[bool, str]:
    """read a single mimetype-and-counter string from source

    Returns whether the source is EOF and the extracted string (or empty one)"""
    params = ""
    eof, mtcStr = getline(src, ";")  # pyright: ignore
    if mtcStr.find("=") == -1:
        while params.count("=") != 2:  # noqa: PLR2004
            eof, params = getline(src, ";")  # pyright: ignore
            if params.count("=") == 2:  # noqa: PLR2004
                mtcStr += ";" + params
            if eof:
                break
    return eof, mtcStr


def parseASingleMimetypeCounter(string: str) -> MimetypeAndCounter:
    """MimetypeAndCounter from a single mimetype-and-counter string"""
    k: int = string.rfind("=")
    if k != len(string) - 1:
        mimeType = string[:k]
        counter = string[k + 1 :]  # noqa: E203
        try:
            return MimetypeAndCounter(mimeType, int(counter))
        except ValueError:
            pass  # value is not castable to int
    return MimetypeAndCounter("", 0)


def parseMimetypeCounter(
    counterData: str,
) -> CounterMap:
    """Mapping of MIME types with count for each from ZIM Counter metadata string"""
    counters = {}
    ss = io.StringIO(counterData)
    eof = False
    while not eof:
        eof, mtcStr = readFullMimetypeAndCounterString(ss)
        mtc = parseASingleMimetypeCounter(mtcStr)
        if mtc.mimetype:
            counters.update([mtc])
    ss.close()
    return counters
