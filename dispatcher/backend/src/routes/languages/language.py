from flask import request, jsonify

from common.mongo import Schedules
from routes.base import BaseRoute
from common.schemas.parameters import SkipLimit500Schema


class LanguagesRoute(BaseRoute):
    rule = "/"
    name = "languages"
    methods = ["GET"]

    def get(self, *args, **kwargs):
        """return a list of languages"""

        request_args = SkipLimit500Schema().load(request.args.to_dict())
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
