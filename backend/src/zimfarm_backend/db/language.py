import pycountry
from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.common.schemas.models import LanguageSchema
from zimfarm_backend.db import count_from_stmt
from zimfarm_backend.db.exceptions import RecordDoesNotExistError
from zimfarm_backend.db.models import Schedule


class LanguageListResult(BaseModel):
    """Result of query to list languages from the database."""

    nb_languages: int
    languages: list[LanguageSchema]


def get_language_from_code(language_code: str) -> LanguageSchema:
    """Get language information from a language code."""
    language = pycountry.languages.get(alpha_3=language_code)

    if not language:
        raise RecordDoesNotExistError(
            f"Language code '{language_code}' not found",
        )

    return LanguageSchema(
        code=language.alpha_3,
        name=language.name,
    )


def get_languages(
    session: OrmSession,
    skip: int,
    limit: int,
) -> LanguageListResult:
    """Get a paginated list of languages from schedules."""
    query = (
        select(Schedule.language_code)
        .distinct(Schedule.language_code)  # distinct on language_code
        .order_by(Schedule.language_code, Schedule.id)
    )

    languages: list[LanguageSchema] = []
    for (language_code,) in session.execute(query.offset(skip).limit(limit)).all():
        try:
            language = get_language_from_code(language_code)
        except RecordDoesNotExistError:
            # omit languages that are invalid
            pass
        else:
            languages.append(language)

    return LanguageListResult(
        nb_languages=count_from_stmt(session, query),
        languages=sorted(
            languages,
            key=lambda language: (language.name, language.code),
        ),
    )
