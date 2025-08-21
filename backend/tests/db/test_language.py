import pytest
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.db.language import get_languages
from zimfarm_backend.db.models import Schedule


def test_get_languages_empty(dbsession: OrmSession):
    """Test getting languages when no schedules exist."""
    results = get_languages(dbsession, skip=0, limit=100)
    assert results.nb_languages == 0
    assert len(results.languages) == 0


@pytest.fixture
def english_schedule(dbsession: OrmSession):
    """Create a test schedule with English language code."""
    schedule = Schedule(
        language_code="eng",
        language_name_en="English",
        language_name_native="English",
        name="test",
        category="test",
        config={"test": "test"},
        enabled=True,
        tags=["test"],
        periodicity="test",
        notification={"test": "test"},
    )
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
    assert results.languages[0].name_en == english_schedule.language_name_en
    assert results.languages[0].name_native == english_schedule.language_name_native


def test_get_languages_duplicate(dbsession: OrmSession):
    """Test getting languages with duplicate language codes but different names."""
    # Create test schedules with same language code but different names
    schedule1 = Schedule(
        language_code="eng",
        language_name_en="English",
        language_name_native="English",
        name="test",
        category="test",
        config={"test": "test"},
        enabled=True,
        tags=["test"],
        periodicity="test",
        notification={"test": "test"},
    )
    schedule2 = Schedule(
        language_code="eng",
        language_name_en="English (US)",
        language_name_native="English (US)",
        name="test2",
        category="test",
        config={"test": "test"},
        enabled=True,
        tags=["test"],
        periodicity="test",
        notification={"test": "test"},
    )
    dbsession.add_all([schedule1, schedule2])
    dbsession.flush()

    # Get languages - should only return one entry due to distinct
    results = get_languages(dbsession, skip=0, limit=100)
    assert results.nb_languages == 1
    assert len(results.languages) == 1


def test_get_languages_pagination(dbsession: OrmSession):
    """Test getting languages with pagination."""
    # Create test schedules
    schedules = [
        Schedule(
            language_code=f"lg{i}",
            language_name_en=f"Language {i}",
            language_name_native=f"Language {i}",
            name=f"test{i}",
            category="test",
            config={"test": "test"},
            enabled=True,
            tags=["test"],
            periodicity="test",
            notification={"test": "test"},
        )
        for i in range(5)
    ]
    dbsession.add_all(schedules)
    dbsession.flush()

    # Test first page
    results = get_languages(dbsession, skip=0, limit=2)
    assert results.nb_languages == 5
    assert len(results.languages) == 2
