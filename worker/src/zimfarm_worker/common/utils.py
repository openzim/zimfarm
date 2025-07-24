# vim: ai ts=4 sts=4 et sw=4 nu

import humanfriendly


def short_id(task_id: str) -> str:
    """stripped version of task_id for containers/display"""
    return task_id[:5]


def as_pos_int(value: int) -> int:
    return 0 if value < 0 else value


def format_size(value: float) -> str:
    return humanfriendly.format_size(value, binary=True)


def format_key(fingerprint: str) -> str:
    """UUID-hex looking from RSA fingerprint"""
    return (
        f"{fingerprint[0:8]}-{fingerprint[8:12]}-{fingerprint[12:16]}"
        f"-{fingerprint[16:20]}-{fingerprint[20:]}"
    ).upper()
