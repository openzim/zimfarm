from flask import request, jsonify

from common.mongo import Schedules
from routes.base import BaseRoute


class tagsRoute(BaseRoute):
    rule = "/"
    name = "tags"
    methods = ["GET"]

    def get(self, *args, **kwargs):
        """return a list of tags"""

        # unpack url parameters
        skip = request.args.get("skip", default=0, type=int)
        limit = request.args.get("limit", default=20, type=int)
        skip = 0 if skip < 0 else skip
        limit = 20 if limit <= 0 else limit

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
