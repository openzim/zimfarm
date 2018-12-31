from datetime import datetime

import pytest
import pytz
from bson import ObjectId


@pytest.fixture(scope='module')
def make_beat_crontab():
    def _make_beat_crontab(minute='*', hour='*', day_of_week='*', day_of_month='*', month_of_year='*') -> dict:
        return {
            'type': 'crontab',
            'config': {
                'minute': minute,
                'hour': hour,
                'day_of_week': day_of_week,
                'day_of_month': day_of_month,
                'month_of_year': month_of_year
            }
        }
    return _make_beat_crontab


@pytest.fixture(scope='module')
def make_offliner_mwoffliner():
    def _make_offliner_mwoffliner(language: str = 'en') -> dict:
        return {
            'name': 'mwoffliner',
            'config': {
                'mwUrl': 'https://{}.wikipedia.org/'.format(language),
                'adminEmail': 'test@kiwix.org'
            }
        }
    return _make_offliner_mwoffliner


@pytest.fixture(scope='module')
def make_schedule(database, make_beat_crontab, make_offliner_mwoffliner):
    schedule_ids = []

    def _make_schedule(name: str, language: str, category: str, beat: dict = None) -> dict:
        document = {
            '_id': ObjectId(),
            'name': name,
            'language': language,
            'category': category,
            'queue': 'tiny',
            'enabled': True,
            'total_run': 10,
            'last_run': datetime(2018, 12, 1, 10, 35, 00, tzinfo=pytz.utc),
            'beat': beat or make_beat_crontab(),
            'offline': make_offliner_mwoffliner(),
            'task': {
                'name': 'mwoffliner'
            }
        }
        schedule_id = database.schedules.insert_one(document).inserted_id
        schedule_ids.append(schedule_id)
        return document

    yield _make_schedule

    database.schedules.delete_many({'_id': {'$in': schedule_ids}})


@pytest.fixture(scope='module')
def schedule(make_schedule, make_beat_crontab):
    beat = make_beat_crontab(minute='0', hour='15', day_of_month='*/5')
    return make_schedule('name', 'language', 'wikipedia', beat)
