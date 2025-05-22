import sqlalchemy as sa
import sqlalchemy.orm as so
from flask import jsonify, request

import db.models as dbm
from common.schemas.parameters import SkipLimitSchema
from db import count_from_stmt, dbsession
from routes.base import BaseRoute


class tagsRoute(BaseRoute):
    rule = "/"
    name = "tags"
    methods = ["GET"]

    @dbsession
    def get(self, session: so.Session, *args, **kwargs):
        """return a list of tags"""

        request_args = SkipLimitSchema().load(request.args.to_dict())
        skip, limit = request_args["skip"], request_args["limit"]

        stmt = (
            sa.select(sa.func.unnest(dbm.Schedule.tags).label("tag"))
            .distinct()
            .order_by("tag")
        )

        nb_tags = count_from_stmt(session, stmt)

        return jsonify(
            {
                "meta": {"skip": skip, "limit": limit, "count": nb_tags},
                "items": list(
                    map(
                        lambda x: x[0],
                        session.execute(stmt.offset(skip).limit(limit)).all(),
                    )
                ),
            }
        )
