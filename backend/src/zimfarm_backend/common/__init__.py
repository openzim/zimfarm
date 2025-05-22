import datetime
from collections import defaultdict
from typing import ClassVar

import pytz


def getnow():
    """naive UTC now"""
    return datetime.datetime.now(datetime.UTC)


def to_naive_utc(timestamp_or_iso: datetime.datetime | int | str) -> datetime.datetime:
    """naive UTC datetime from iso string or timestamp"""
    if isinstance(timestamp_or_iso, str):
        new_date = datetime.datetime.fromisoformat(timestamp_or_iso)
    elif isinstance(timestamp_or_iso, int):
        new_date = datetime.datetime.fromtimestamp(timestamp_or_iso)
    else:
        new_date = timestamp_or_iso

    return new_date.astimezone(pytz.utc).replace(tzinfo=None)


class WorkersIpChangesCounts:
    today: datetime.date = datetime.datetime.now(datetime.UTC).date()
    counts: ClassVar[dict[str, int]] = defaultdict(int)

    @classmethod
    def reset(cls):
        cls.today = datetime.datetime.now(datetime.UTC).date()
        cls.counts = defaultdict(int)

    @classmethod
    def add(cls, worker: str) -> int:
        cls.counts[worker] += 1
        return cls.get(worker)

    @classmethod
    def get(cls, worker: str) -> int:
        return cls.counts.get(worker, 0)
