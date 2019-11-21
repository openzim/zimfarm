from flask import request, jsonify
import trafaret

from common.mongo import Schedules
from routes.base import BaseRoute


class tagsRoute(BaseRoute):
    rule = "/"
    name = "tags"
    methods = ["GET"]

    def get(self, *args, **kwargs):
        """return a list of tags"""

        # unpack url parameters
        request_args = request.args.to_dict()
        validator = trafaret.Dict(
            {
                trafaret.Key("skip", default=0): trafaret.ToInt(gte=0),
                trafaret.Key("limit", default=20): trafaret.ToInt(gt=0, lte=200),
            }
        )
        request_args = validator.check(request_args)

        # unpack query parameter
        skip, limit = request_args["skip"], request_args["limit"]

        base_pipeline = [
            {"$project": {"_id": 0, "tags": 1}},
            {"$unwind": "$tags"},
            {"$group": {"_id": "$tags"}},
        ]

        try:
            nb_tags = next(
                Schedules().aggregate(base_pipeline + [{"$count": "count"}])
            )["count"]
        except StopIteration:
            nb_tags = 0

        if nb_tags == 0:
            tags = []
        else:
            pipeline = base_pipeline + [
                {"$sort": {"_id": 1}},
                {"$skip": skip},
                {"$limit": limit},
            ]

            tags = [t["_id"] for t in Schedules().aggregate(pipeline)]

        return jsonify(
            {"meta": {"skip": skip, "limit": limit, "count": nb_tags}, "items": tags}
        )
