import sqlalchemy as sa
import sqlalchemy.orm as so
from flask import jsonify, request

import db.models as dbm
from common.schemas.parameters import SkipLimit500Schema
from db import count_from_stmt, dbsession
from routes.base import BaseRoute


class LanguagesRoute(BaseRoute):
    rule = "/"
    name = "languages"
    methods = ["GET"]

    @dbsession
    def get(self, session: so.Session, *args, **kwargs):
        """return a list of languages"""

        request_args = SkipLimit500Schema().load(request.args.to_dict())
        skip, limit = request_args["skip"], request_args["limit"]

        # we select the distinct languages from schedules:
        # - we need the distinct on language code to select only one if there is a case
        #   where two schedules have different name_en or name_native for the same
        #   language_code
        # - we also sort by schedule id just to have a consistent result if the
        #   condition above arises
        stmt = (
            sa.select(
                dbm.Schedule.language_code,
                dbm.Schedule.language_name_en,
                dbm.Schedule.language_name_native,
            )
            .distinct(dbm.Schedule.language_code)  # distinct on language_code
            .order_by(dbm.Schedule.language_code, dbm.Schedule.id)
        )

        nb_languages = count_from_stmt(session, stmt)

        return jsonify(
            {
                "meta": {"skip": skip, "limit": limit, "count": nb_languages},
                "items": list(
                    map(
                        lambda x: {"code": x[0], "name_en": x[1], "name_native": x[2]},
                        session.execute(stmt.offset(skip).limit(limit)).all(),
                    )
                ),
            }
        )
