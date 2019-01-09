import pytest
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
def make_celery():
    def _make_celery() -> dict:
        return {
            'task_name': 'offliner.mwoffliner',
            'queue': 'offliner_default'
        }
    return _make_celery


@pytest.fixture(scope='module')
def make_language():
    def _make_language(code: str = 'en', name_en: str = 'language_en', name_native: str = 'language_native') -> dict:
        return {
            'code': code,
            'name_en': name_en,
            'name_native': name_native
        }
    return _make_language


@pytest.fixture(scope='module')
def make_task_mwoffliner():
    def _make_task_mwoffliner(sub_domain: str = 'en', admin_email: str = 'test@kiwix.org',
                              format: str = 'nopic') -> dict:
        return {
            'image_name': 'openzim/mwoffliner',
            'image_tag': 'latest',
            'warehouse_path': '/wikipedia',
            'config': {
                'mwUrl': 'https://{}.wikipedia.org'.format(sub_domain),
                'adminEmail': admin_email,
                'format': format,
                'withZimFullTextIndex': True
            }
        }
    return _make_task_mwoffliner


@pytest.fixture(scope='module')
def make_schedule(database, make_beat_crontab, make_celery, make_language, make_task_mwoffliner):
    schedule_ids = []

    def _make_schedule(name: str, category: str,
                       beat: dict = None, task: dict = None) -> dict:
        document = {
            '_id': ObjectId(),
            'name': name,
            'category': category,
            'enabled': True,
            'beat': beat or make_beat_crontab(),
            'celery': make_celery(),
            'language': make_language(),
            'tags': ['nopic'],
            'task': task or make_task_mwoffliner()
        }
        print(document)
        schedule_id = database.schedules.insert_one(document).inserted_id
        schedule_ids.append(schedule_id)
        return document

    yield _make_schedule

    database.schedules.delete_many({'_id': {'$in': schedule_ids}})


@pytest.fixture(scope='module')
def schedule(make_schedule, make_beat_crontab, make_task_mwoffliner):
    beat = make_beat_crontab(minute='0', hour='15', day_of_month='*/5')
    task = make_task_mwoffliner(sub_domain='en')
    return make_schedule('name', 'wikipedia', beat, task)
