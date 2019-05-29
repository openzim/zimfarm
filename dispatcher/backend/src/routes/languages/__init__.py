from routes.base import BaseBlueprint
from routes.languages.language import LanguagesRoute


class Blueprint(BaseBlueprint):
    def __init__(self):
        super().__init__('languages', __name__, url_prefix='/api/languages')

        self.register_route(LanguagesRoute())
