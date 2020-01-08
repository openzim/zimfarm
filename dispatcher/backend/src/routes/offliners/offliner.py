from flask import jsonify

from common.enum import Offliner
from routes import url_object_id
from routes.base import BaseRoute
from routes.errors import NotFound
from common.schemas.models import ScheduleConfigSchema


class offlinersRoute(BaseRoute):
    rule = "/"
    name = "offliners"
    methods = ["GET"]

    def get(self, *args, **kwargs):
        """return a list of tags"""

        offliners = Offliner.all()

        return jsonify(
            {
                "meta": {"skip": 0, "limit": 100, "count": len(offliners)},
                "items": offliners,
            }
        )


class offlinerRoute(BaseRoute):
    rule = "/<string:offliner>"
    name = "offliner"
    methods = ["GET", "POST", "PATCH"]

    @url_object_id("offliner")
    def get(self, offliner: str, *args, **kwargs):

        if offliner not in Offliner.all():
            raise NotFound()

        schema = ScheduleConfigSchema.get_offliner_schema(offliner)()

        return jsonify(schema.to_desc())
