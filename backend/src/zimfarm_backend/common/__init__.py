import datetime
from collections import defaultdict
from typing import ClassVar
from uuid import UUID

import pytz


def getnow():
    """naive UTC now"""
    return datetime.datetime.now(datetime.UTC).replace(tzinfo=None)


def to_naive_utc(timestamp_or_iso: datetime.datetime | int | str) -> datetime.datetime:
    """naive UTC datetime from iso string or timestamp"""
    if isinstance(timestamp_or_iso, str):
        new_date = datetime.datetime.fromisoformat(timestamp_or_iso)
    elif isinstance(timestamp_or_iso, int):
        new_date = datetime.datetime.fromtimestamp(timestamp_or_iso)
    else:
        new_date = timestamp_or_iso

    return new_date.astimezone(pytz.utc).replace(tzinfo=None)


def is_valid_uuid(identifier: str) -> bool:
    """Check if string is a valid UUID"""
    try:
        UUID(identifier)
    except ValueError:
        return False
    return True


class WorkersIpChangesCounts:
    today: datetime.date = getnow().date()
    counts: ClassVar[dict[str, int]] = defaultdict(int)

    @classmethod
    def reset(cls):
        cls.today = getnow()
        cls.counts = defaultdict(int)

    @classmethod
    def add(cls, worker: str) -> int:
        cls.counts[worker] += 1
        return cls.get(worker)

    @classmethod
    def get(cls, worker: str) -> int:
        return cls.counts.get(worker, 0)
