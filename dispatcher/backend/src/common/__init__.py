import datetime

import pytz


def getnow():
    """ naive UTC now """
    return datetime.datetime.utcnow()


def to_naive_utc(isodate):
    return datetime.fromisoformat(isodate).astimezone(pytz.utc).replace(tzinfo=None)
