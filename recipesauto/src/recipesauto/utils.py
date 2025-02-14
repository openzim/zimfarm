import re

name_pattern = re.compile(r"^[a-zA-Z0-9\.\-]*_[a-zA-Z0-9\.\-]*_[a-zA-Z0-9\.\-]*_?[a-zA-Z0-9\.\-]*$")

def check_zim_name(zim_name: str):
    if not name_pattern.match(zim_name):
        raise Exception(f"Bad zim name: {zim_name}")
    return zim_name
    
