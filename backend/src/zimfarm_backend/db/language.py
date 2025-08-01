from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.common.schemas.models import LanguageSchema
from zimfarm_backend.db import count_from_stmt
from zimfarm_backend.db.models import Schedule


class LanguageListResult(BaseModel):
    """Result of query to list languages from the database."""

    nb_languages: int
    languages: list[LanguageSchema]


def get_languages(
    session: OrmSession,
    skip: int,
    limit: int,
) -> LanguageListResult:
    """Get a paginated list of languages from schedules."""
    query = (
        select(
            Schedule.language_code,
            Schedule.language_name_en,
            Schedule.language_name_native,
        )
        .distinct(Schedule.language_code)  # distinct on language_code
        .order_by(Schedule.language_code, Schedule.id)
    )

    return LanguageListResult(
        nb_languages=count_from_stmt(session, query),
        languages=sorted(
            [
                LanguageSchema.model_validate(
                    {
                        "code": language_code,
                        "name_en": language_name_en,
                        "name_native": language_name_native,
                    },
                    context={"skip_validation": True},
                )
                for (
                    language_code,
                    language_name_en,
                    language_name_native,
                ) in session.execute(query.offset(skip).limit(limit)).all()
            ],
            key=lambda language: (language.name_en, language.code),
        ),
    )
