import json
from random import randint

from sshtunnel import SSHTunnelForwarder
from pymongo import MongoClient


class Schedule:
    def __init__(self, language_code: str, language_name: str, language_name_en: str,  category: str, mw_url: str):
        self.language_code = language_code
        self.language_name = language_name
        self.language_name_en = language_name_en
        self.category = category
        self.mw_url = mw_url

    @property
    def name(self):
        underscored_name = self.language_name_en.replace(' ', '_')
        return f'{self.category}_{underscored_name}'

    def generate_offliner(self):
        return {
            'name': 'mwoffliner',
            'config': {
                'mwUrl': self.mw_url,
                'adminEmail': 'chris@kiwix.org'
            }
        }

    def generate_beat(self):
        config = {
            'minute': str(randint(0, 3) * 15),
            'hour': str(randint(0, 23)),
            'day_of_month': str(randint(0, 28)),
            'day_of_week': '*',
            'month_of_year': '*'}
        return {
            'type': 'crontab',
            'config': config
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
            'offliner': self.generate_offliner(),
            'beat': self.generate_beat(),
            'task': {
                'name': 'mwoffliner',
                'queue': 'offliner_default'
            }
        }


class Parser:
    def __init__(self, path):
        self.data = self.read_file(path)
        self.schedules = {}

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
                break
            else:
                self.process_one_matrix(value)

        print(f'Processing Finished, total: {count}, schedules: {len(self.schedules)}, special: {special_count}')

    def process_one_matrix(self, matrix: dict):
        language_code = matrix.get('code')
        language_name = matrix.get('name')
        language_name_en = matrix.get('localname')
        if language_code is None or language_name is None:
            return

        sites = matrix.get('site', [])
        for site in sites:
            mw_url = site.get('url')  # https://aa.wikipedia.org
            site_code = site.get('code')  # wikipedia, etc
            site_code = 'wikipedia' if site_code == 'wiki' else site_code

            schedule = Schedule(language_code, language_name, language_name_en, site_code, mw_url)
            if schedule.name not in self.schedules:
                self.schedules[schedule.name] = schedule.generate_document()
            else:
                print(f'{schedule.name} already exist')


class RemoteDatabase:
    pass


if __name__ == '__main__':
    parser = Parser(path='./mwoffliner_site_matrix.json')
    parser.parse()

    with SSHTunnelForwarder(
            'farm.openzim.org',
            ssh_username='chris',
            ssh_pkey="/Users/chrisli/.ssh/id_rsa",
            remote_bind_address=('127.0.0.1', 27017),
            local_bind_address=('0.0.0.0', 27017)
    ) as tunnel:
        with MongoClient() as client:
            collection = client['Zimfarm']['schedules']
            index = 0
            for schedule_name, schedule_doc in parser.schedules.items():
                print(f'{index}/{len(parser.schedules)}-{round(index/len(parser.schedules), 4)}', schedule_name)
                collection.update_one({'name': schedule_name}, {'$set': schedule_doc}, upsert=True)

                index += 1

    print('FINISH!')
