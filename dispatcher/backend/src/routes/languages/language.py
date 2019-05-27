import json
from http import HTTPStatus

import trafaret as t
from flask import request, Response, jsonify

from common.mongo import Languages
from errors.http import InvalidRequestJSON
from routes import authenticate, errors
from routes.base import BaseRoute
from routes.languages.base import LanguageQueryMixin


class LanguagesRoute(BaseRoute):
    rule = '/'
    name = 'languages'
    methods = ['POST', 'GET']

    @authenticate
    def post(self, *args, **kwargs):
        """Create language"""

        request_json = request.get_json()
        if not request_json:
            raise InvalidRequestJSON()

        # validate schema
        validator = t.Dict(
            t.Key('code', optional=False, trafaret=t.String(allow_blank=False)),
            t.Key('name_en', optional=False, trafaret=t.String(allow_blank=False)),
            t.Key('name_native', optional=False, trafaret=t.String(allow_blank=False)))
        try:
            validator.check(request_json)
        except t.DataError as error:
            raise errors.BadRequest(str(error))

        # ensure not a duplicate
        if Languages().find_one({"code": request_json["code"]}):
            raise errors.BadRequest(
                "language with code `{}` already exists.".format(request_json['code']))

        # insert in db
        language_id = Languages().insert_one(request_json).inserted_id

        return Response(json.dumps({'_id': str(language_id)}), HTTPStatus.CREATED)

    @authenticate
    def get(self, *args, **kwargs):
        """return a list of languages"""

        # unpack url parameters
        skip = request.args.get('skip', default=0, type=int)
        limit = request.args.get('limit', default=100, type=int)
        skip = 0 if skip < 0 else skip
        limit = 100 if limit <= 0 else limit

        query = {}
        cursor = Languages().find(query).skip(skip).limit(limit)
        count = Languages().count_documents(query)
        languages = [language for language in cursor]

        return jsonify({
            'meta': {
                'skip': skip,
                'limit': limit,
                'count': count,
            },
            'items': languages
        })


class LanguageRoute(BaseRoute, LanguageQueryMixin):
    rule = '/<string:language_id>'
    name = 'language'
    methods = ['GET', 'PATCH', 'DELETE']

    @authenticate
    def get(self, language_id: str, *args, **kwargs):
        """get a single language"""

        query = self.get_language_query(language_id)
        language = Languages().find_one(query)
        if language is None:
            raise errors.NotFound()

        return jsonify(language)

    @authenticate
    def patch(self, language_id: str, *args, **kwargs):
        """edit a single language"""

        query = self.get_language_query(language_id)
        if Languages().find_one(query) is None:
            raise errors.NotFound()

        request_json = request.get_json()
        if not request_json:
            raise InvalidRequestJSON()

        # validate schema
        validator = t.Dict(
            t.Key('name_en', optional=False, trafaret=t.String(allow_blank=False)),
            t.Key('name_native', optional=False, trafaret=t.String(allow_blank=False)))
        try:
            validator.check(request_json)
        except t.DataError as error:
            raise errors.BadRequest(str(error))

        # update in db
        matched_count = Languages().update_one(query, {'$set': request_json})

        if not matched_count:
            raise errors.NotFound()

        return Response('', HTTPStatus.NO_CONTENT)

    @authenticate
    def delete(self, language_id: str, *args, **kwargs):
        """delete a language"""

        query = self.get_language_query(language_id)
        result = Languages().delete_one(query)

        if result.deleted_count == 0:
            raise errors.NotFound()

        return '', HTTPStatus.NO_CONTENT
