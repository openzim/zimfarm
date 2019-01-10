import json
from random import randint

from sshtunnel import SSHTunnelForwarder
from pymongo import MongoClient
from pymongo.collection import Collection


class Schedule:
    def __init__(self, language_code: str, language_name: str, language_name_en: str,
                 category_code: str, category_name: str, mw_url: str):
        self.language_code = language_code
        self.language_name = language_name
        self.language_name_en = language_name_en
        self.category_code = category_code
        self.category_name = category_name
        self.mw_url = mw_url

        self.beat = self.generate_beat()

    @property
    def name(self):
        return f'{self.category_name}_{self.language_code}'

    def generate_beat(self):
        config = {
            'minute': str(randint(0, 5) * 10),
            'hour': str(randint(0, 23)),
            'day_of_month': str(randint(1, 28)),
            'day_of_week': '*',
            'month_of_year': '*'}
        return {
            'type': 'crontab',
            'config': config}

    def generate_task_config(self):
        return {
            'config': {
                'mwUrl': self.mw_url,
                'adminEmail': 'contact@kiwix.org'
            },
            'warehouse_path': self.category
        }

    def generate_document(self) -> dict:
        return {
            'name': self.name,
            'enabled': False,
            'category': self.category,
            'language': {
                'code': self.language_code,
                'name_native': self.language_name,
                'name_en': self.language_name_en
            },
            'beat': self.generate_beat(),
            'task': self.generate_task_config(),
            'celery': {
                'task_name': 'offliner.mwoffliner',
                'queue': 'offliner_default'
            }
        }


class Beat:
    @staticmethod
    def generate_once_per_month():
        return {
            'type': 'crontab',
            'config': {
                'minute': str(randint(0, 3) * 15),
                'hour': str(randint(0, 23)),
                'day_of_month': str(randint(1, 28)),
                'day_of_week': '*',
                'month_of_year': '*'
            }
        }


class Celery:
    @staticmethod
    def generate():
        return {
            'task_name': 'offliner.mwoffliner',
            'queue': 'offliner_default'
        }


class TaskConfig:
    @staticmethod
    def generate(mw_url, category, format):
        return {
            'config': {
                'mwUrl': mw_url,
                'adminEmail': 'contact@kiwix.org',
                'format': format,
                'withZimFullTextIndex': True
            },
            'image_tag': 'latest',
            'warehouse_path': f'/{category}'
        }


class Language:
    @staticmethod
    def generate(code: str, name: str, name_en: str):
        return {
            'code': code,
            'name_native': name,
            'name_en': name_en
        }


class Parser:
    def __init__(self, path, collection: Collection):
        self.data = self.read_file(path)
        self.schedules = {}
        self.collection = collection

    def read_file(self, path):
        with open(path, 'r') as file:
            return json.load(file)

    def parse(self):
        sitematrix = self.data.get('sitematrix', {})
        count = 0
        special_count = 0

        for key, value in sitematrix.items():
            if key == 'count':
                count = value
            elif key == 'specials':
                special_count = len(value)
            else:
                self.process_one_language(value)

        print(f'Processing Finished, total: {count}, schedules: {count - special_count}, special: {special_count}')

    def process_one_language(self, matrix: dict):
        language_code = matrix.get('code')
        language_name = matrix.get('name')
        language_name_en = matrix.get('localname')

        sites = matrix.get('site', [])
        for site in sites:
            mw_url = site.get('url')  # https://aa.wikipedia.org
            site_code = site.get('code')  # wikipedia, etc
            site_code = 'wikipedia' if site_code == 'wiki' else site_code
            site_name = site_code.capitalize()

            beat = Beat.generate_once_per_month()
            language = Language.generate(language_code, language_name, language_name_en)
            celery = Celery.generate()

            tags = ['nodet', 'nopic', 'novid']
            for tag in tags:
                task_config = TaskConfig.generate(mw_url, site_code, tag)
                name = f'{site_name}_{language_code}_{tag}'
                schedule = {
                    'name': name,
                    'enabled': False,
                    'category': site_code,
                    'tags': [tag],
                    'beat': beat,
                    'celery': celery,
                    'language': language,
                    'task': task_config
                }

                self.collection.update_one({'name': schedule['name']}, {'$set': schedule}, upsert=True)
                self.log_progress(language_code, name)

    def log_progress(self, language_code, name):
        print(f'processing {language_code} {name}')


def parse_and_save():
    with MongoClient() as client:
        collection = client['Zimfarm']['schedules']
        parser = Parser('./mwoffliner_site_matrix.json', collection)
        parser.parse()


if __name__ == '__main__':
    # parse_and_save()
    with SSHTunnelForwarder(
            'farm.openzim.org',
            ssh_username='chris',
            ssh_pkey="/Users/chrisli/.ssh/id_rsa",
            remote_bind_address=('127.0.0.1', 27017),
            local_bind_address=('0.0.0.0', 27017)
    ) as tunnel:
        parse_and_save()
    print('FINISH!')
