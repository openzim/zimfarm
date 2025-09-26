from collections.abc import Callable

import pytest
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.common.schemas.models import ScheduleConfigSchema
from zimfarm_backend.common.schemas.orms import OfflinerDefinitionSchema, OfflinerSchema
from zimfarm_backend.db.exceptions import RecordDoesNotExistError
from zimfarm_backend.db.language import get_language_from_code, get_languages
from zimfarm_backend.db.models import Schedule
from zimfarm_backend.db.schedule import create_schedule_full_schema, get_schedule


def test_get_languages_empty(dbsession: OrmSession):
    """Test getting languages when no schedules exist."""
    results = get_languages(dbsession, skip=0, limit=100)
    assert results.nb_languages == 0
    assert len(results.languages) == 0


@pytest.fixture
def english_schedule(
    dbsession: OrmSession, mwoffliner_definition: OfflinerDefinitionSchema
):
    """Create a test schedule with English language code."""
    schedule = Schedule(
        language_code="eng",
        name="test",
        category="test",
        config={"test": "test"},
        enabled=True,
        tags=["test"],
        periodicity="test",
        notification={"test": "test"},
    )
    schedule.offliner_definition_id = mwoffliner_definition.id
    dbsession.add(schedule)
    dbsession.flush()
    return schedule


def test_get_languages_single(dbsession: OrmSession, english_schedule: Schedule):
    """Test getting languages with a single schedule."""
    results = get_languages(dbsession, skip=0, limit=100)
    assert results.nb_languages == 1
    assert len(results.languages) == 1
    # Check that the returned language is the English schedule
    assert results.languages[0].code == english_schedule.language_code
    # The name should come from pycountry, not the database
    assert results.languages[0].name == "English"


def test_get_languages_pagination(
    dbsession: OrmSession, mwoffliner_definition: OfflinerDefinitionSchema
):
    """Test getting languages with pagination."""
    # Create test schedules with valid language codes
    schedules = [
        Schedule(
            language_code="eng",  # English
            name="test1",
            category="test",
            config={"test": "test"},
            enabled=True,
            tags=["test"],
            periodicity="test",
            notification={"test": "test"},
        ),
        Schedule(
            language_code="fra",  # French
            name="test2",
            category="test",
            config={"test": "test"},
            enabled=True,
            tags=["test"],
            periodicity="test",
            notification={"test": "test"},
        ),
        Schedule(
            language_code="spa",  # Spanish
            name="test3",
            category="test",
            config={"test": "test"},
            enabled=True,
            tags=["test"],
            periodicity="test",
            notification={"test": "test"},
        ),
        Schedule(
            language_code="eng",  # English
            name="test4",
            category="test",
            config={"test": "test"},
            enabled=True,
            tags=["test"],
            periodicity="test",
            notification={"test": "test"},
        ),
        Schedule(
            language_code="spa",  # Spanish
            name="test5",
            category="test",
            config={"test": "test"},
            enabled=True,
            tags=["test"],
            periodicity="test",
            notification={"test": "test"},
        ),
    ]
    for schedule in schedules:
        schedule.offliner_definition_id = mwoffliner_definition.id
    dbsession.add_all(schedules)
    dbsession.flush()

    results = get_languages(dbsession, skip=0, limit=2)
    assert results.nb_languages == 3
    assert len(results.languages) == 2


def test_get_invalid_languages(
    dbsession: OrmSession, mwoffliner_definition: OfflinerDefinitionSchema
):
    """Test getting languages with invalid codes"""
    schedules = [
        Schedule(
            language_code="en",  # English
            name="test1",
            category="test",
            config={"test": "test"},
            enabled=True,
            tags=["test"],
            periodicity="test",
            notification={"test": "test"},
        ),
        Schedule(
            language_code="fr",  # French
            name="test2",
            category="test",
            config={"test": "test"},
            enabled=True,
            tags=["test"],
            periodicity="test",
            notification={"test": "test"},
        ),
        Schedule(
            language_code="jp",  # Japanase
            name="test3",
            category="test",
            config={"test": "test"},
            enabled=True,
            tags=["test"],
            periodicity="test",
            notification={"test": "test"},
        ),
    ]
    for schedule in schedules:
        schedule.offliner_definition_id = mwoffliner_definition.id
    dbsession.add_all(schedules)
    dbsession.flush()

    results = get_languages(dbsession, skip=0, limit=5)
    # even though we have three distinct languages in the db, none is returned
    # as they fail validation constraints
    assert results.nb_languages == 3
    assert len(results.languages) == 0


@pytest.mark.parametrize(
    "code",
    ["en", "fr", "invalid"],
)
def test_get_schedule_with_invalid_language_from_db(
    dbsession: OrmSession,
    create_schedule_config: Callable[..., ScheduleConfigSchema],
    mwoffliner_definition: OfflinerDefinitionSchema,
    mwoffliner: OfflinerSchema,
    code: str,
):
    # Create test schedule with invalid language code
    schedule = Schedule(
        language_code=code,
        name="test1",
        category="test",
        config=create_schedule_config().model_dump(mode="json"),
        enabled=True,
        tags=["test"],
        periodicity="test",
        notification={"test": "test"},
    )
    schedule.offliner_definition_id = mwoffliner_definition.id
    dbsession.add(schedule)
    dbsession.flush()
    # assert we can read schedules with invalid codes from db
    schedule = get_schedule(dbsession, schedule_name="test1")
    assert schedule.language_code == code
    schedule_schema = create_schedule_full_schema(schedule, mwoffliner)
    # for unknown languages, the code and name should be the same
    assert schedule_schema.language.code == code
    assert schedule_schema.language.name == code


@pytest.mark.parametrize(
    "code,name",
    [
        ("eng", "English"),
        ("fra", "French"),
        ("spa", "Spanish"),
    ],
)
def test_get_language_from_code(code: str, name: str):
    """Test getting language information from language codes."""
    language = get_language_from_code(code)
    assert language.name == name


@pytest.mark.parametrize(
    "code",
    ["en", "fr", "invalid"],
)
def test_get_language_from_code_invalid(code: str):
    """Test getting language information with invalid language codes."""
    with pytest.raises(RecordDoesNotExistError):
        get_language_from_code(code)
