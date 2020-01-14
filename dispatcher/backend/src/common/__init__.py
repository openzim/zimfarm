import datetime

import pytz


def getnow():
    """ naive UTC now """
    return datetime.datetime.utcnow()


def to_naive_utc(timestamp_or_iso):
    """ naive UTC datetime from iso string or timestamp """
    if isinstance(timestamp_or_iso, str):
        new_date = datetime.datetime.fromisoformat(timestamp_or_iso)
    elif isinstance(timestamp_or_iso, int):
        new_date = datetime.datetime.fromtimestamp(timestamp_or_iso)
    elif isinstance(timestamp_or_iso, datetime.datetime):
        new_date = timestamp_or_iso

    return new_date.astimezone(pytz.utc).replace(tzinfo=None)
