from collections.abc import Callable

from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.db.models import Schedule
from zimfarm_backend.db.tags import get_tags


def test_get_tags_empty(dbsession: OrmSession):
    """Test that get_tags returns empty list when no schedules exist"""
    result = get_tags(dbsession, skip=0, limit=10)
    assert result.nb_records == 0
    assert len(result.tags) == 0


def test_get_tags(
    dbsession: OrmSession,
    create_schedule: Callable[..., Schedule],
):
    """Test that get_tags returns tags from schedules"""
    # Create schedules with different tags
    create_schedule(name="schedule1", tags=["tag1", "tag2"])
    create_schedule(name="schedule2", tags=["tag2", "tag3"])
    create_schedule(name="schedule3", tags=["tag3", "tag4"])
    create_schedule(name="schedule4", tags=["tag4", "tag5"])

    result = get_tags(dbsession, skip=0, limit=2)
    assert result.nb_records == 5
    assert len(result.tags) == 2
    assert sorted(result.tags) == ["tag1", "tag2"]
