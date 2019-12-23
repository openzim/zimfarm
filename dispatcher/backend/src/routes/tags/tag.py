from flask import request, jsonify

from common.mongo import Schedules
from routes.base import BaseRoute
from common.schemas.parameters import SkipLimitSchema


class tagsRoute(BaseRoute):
    rule = "/"
    name = "tags"
    methods = ["GET"]

    def get(self, *args, **kwargs):
        """return a list of tags"""

        request_args = SkipLimitSchema().load(request.args.to_dict())
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
