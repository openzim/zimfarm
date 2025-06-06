import re

from langcodes import Language

name_pattern = re.compile(r"^[a-z0-9\.\-]*_[a-z0-9\.\-]*_[a-z0-9\.\-]*_?[a-z0-9\.\-]*$")


def check_zim_name(zim_name: str):
    if not name_pattern.match(zim_name):
        raise Exception(f"Bad zim name: {zim_name}")
    return zim_name


def get_language_data(code: str) -> dict[str, str]:
    """Returns Zimfarm language data for a given code"""
    language = Language.get(code)
    return {
        "code": code,
        "name_en": language.language_name("en"),
        "name_native": language.language_name(code),
    }
