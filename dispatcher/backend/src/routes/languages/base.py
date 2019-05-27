from bson.objectid import ObjectId, InvalidId


class LanguageQueryMixin:
    @staticmethod
    def get_language_query(language_id_or_code: str):
        try:
            language_id = ObjectId(language_id_or_code)
            return {'_id': language_id}
        except InvalidId:
            language_code = language_id_or_code
            return {'code': language_code}
