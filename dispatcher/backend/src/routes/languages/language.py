import trafaret as t
from flask import request, jsonify

from common.mongo import Schedules
from routes.base import BaseRoute


class LanguagesRoute(BaseRoute):
    rule = "/"
    name = "languages"
    methods = ["GET"]

    def get(self, *args, **kwargs):
        """return a list of languages"""

        request_args = request.args.to_dict()
        validator = t.Dict(
            {
                t.Key("skip", default=0): t.ToInt(gte=0),
                t.Key("limit", default=20): t.ToInt(gt=0, lte=500),
            }
        )
        request_args = validator.check(request_args)
        skip, limit = request_args["skip"], request_args["limit"]

        group = {
            "$group": {
                "_id": "$language.code",
                "name_en": {"$first": "$language.name_en"},
                "name_native": {"$first": "$language.name_native"},
            }
        }

        try:
            nb_languages = next(Schedules().aggregate([group, {"$count": "count"}]))[
                "count"
            ]
        except StopIteration:
            nb_languages = 0

        if nb_languages == 0:
            languages = []
        else:
            pipeline = [
                group,
                {"$sort": {"_id": 1}},
                {"$skip": skip},
                {"$limit": limit},
            ]
            languages = [
                {
                    "code": s["_id"],
                    "name_en": s["name_en"],
                    "name_native": s["name_native"],
                }
                for s in Schedules().aggregate(pipeline)
            ]

        return jsonify(
            {
                "meta": {"skip": skip, "limit": limit, "count": nb_languages},
                "items": languages,
            }
        )
