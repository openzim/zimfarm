import re

import pycountry

name_pattern = re.compile(r"^[a-z0-9\.\-]*_[a-z0-9\.\-]*_[a-z0-9\.\-]*_?[a-z0-9\.\-]*$")


def check_zim_name(zim_name: str):
    if not name_pattern.match(zim_name):
        raise Exception(f"Bad zim name: {zim_name}")
    return zim_name


def get_iso_639_3_code(code: str) -> str | None:
    """Get ISO 639-3 language code for a given code"""
    language = pycountry.languages.get(alpha_3=code)
    # If not found, attempt to get the language code from the ISO 639-1 code
    if not language:
        language = pycountry.languages.get(alpha_2=code)

    if not language:
        return None
    return language.alpha_3
