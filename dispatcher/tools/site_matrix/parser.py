import json


class Schedule:
    def __init__(self, language_code: str, language_name: str, category: str, mw_url: str):
        self.language_code = language_code
        self.language_name = language_name
        self.category = category
        self.mw_url = mw_url

    @staticmethod
    def generate_beat() -> dict:
        return {
            'type': 'crontab',
            'config': {}
        }

    def generate_document(self) -> dict:
        return {
            'category': self.category,
            'language': {

            }
        }


class Parser:
    def __init__(self, path):
        self.data = self.read_file(path)
        self.offliner_configs = []

    def read_file(self, path):
        with open(path, 'r') as file:
            return json.load(file)

    def parse(self):
        sitematrix = self.data.get('sitematrix', {})
        count = 0

        for key, value in sitematrix.items():
            if key == 'count':
                count = value
            else:
                self.process_one_matrix(value)
                break

    def process_one_matrix(self, matrix: dict):
        language_code = matrix.get('code')
        language_name = matrix.get('localname')
        if language_code is None or language_name is None:
            return

        sites = matrix.get('site', [])
        for site in sites:
            mw_url = site.get('url')  # https://aa.wikipedia.org
            site_name = site.get('sitename')  # Wikipedia, etc
            print(mw_url)


        print(matrix)



if __name__ == '__main__':
    parser = Parser(path='./mwoffliner_site_matrix.json')
    parser.parse()