from flask import jsonify

from common.enum import Platform
from routes.base import BaseRoute


class platformsRoute(BaseRoute):
    rule = "/"
    name = "platforms"
    methods = ["GET"]

    def get(self, *args, **kwargs):
        platforms = Platform.all()

        return jsonify(
            {
                "meta": {"skip": 0, "limit": 100, "count": len(platforms)},
                "items": platforms,
            }
        )
