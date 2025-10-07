from collections.abc import Callable

import pytest
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.db.contexts import get_contexts
from zimfarm_backend.db.models import Schedule, Worker


def test_get_contexts_empty(dbsession: OrmSession):
    """Test that get_contexts returns empty list when no contexts exist"""
    result = get_contexts(dbsession, skip=0, limit=10)
    assert result.nb_records == 0
    assert len(result.contexts) == 0


def test_get_contexts_from_schedules(
    dbsession: OrmSession, create_schedule: Callable[..., Schedule]
):
    """Test that get_contexts returns contexts from schedules"""
    # Create schedules with different contexts
    create_schedule(name="schedule1", context="priority")
    create_schedule(name="schedule2", context="general")
    create_schedule(name="schedule3", context="priority")  # duplicate
    create_schedule(name="schedule4", context="")  # empty context should be ignored

    result = get_contexts(dbsession, skip=0, limit=10)
    assert result.nb_records == 2
    assert result.contexts == ["general", "priority"]


def test_get_contexts_from_workers(
    dbsession: OrmSession, create_worker: Callable[..., Worker]
):
    """Test that get_contexts returns contexts from workers"""
    # Create workers with different contexts
    create_worker(name="worker1", contexts={"priority": None, "fast": None})
    create_worker(name="worker2", contexts={"general": None, "slow": None})
    create_worker(name="worker3", contexts={"priority": None})  # duplicate
    create_worker(name="worker4", contexts={})  # empty contexts should be ignored

    result = get_contexts(dbsession, skip=0, limit=10)
    assert result.nb_records == 4
    assert result.contexts == ["fast", "general", "priority", "slow"]


def test_get_contexts_combined(
    dbsession: OrmSession,
    create_schedule: Callable[..., Schedule],
    create_worker: Callable[..., Worker],
):
    """Test that get_contexts returns unique contexts from both schedules and workers"""
    # Create schedules with contexts
    create_schedule(name="schedule1", context="priority")
    create_schedule(name="schedule2", context="general")

    # Create workers with contexts (some overlapping)
    create_worker(name="worker1", contexts={"priority": None, "fast": None})
    create_worker(name="worker2", contexts={"general": None, "slow": None})

    result = get_contexts(dbsession, skip=0, limit=10)
    assert result.nb_records == 4
    assert result.contexts == ["fast", "general", "priority", "slow"]


@pytest.mark.parametrize(
    "skip,limit,expected_results",
    [
        pytest.param(0, 3, 3, id="first-page"),
        pytest.param(3, 3, 3, id="second-page"),
        pytest.param(0, 1, 1, id="first-page-with-low-limit"),
        pytest.param(0, 10, 6, id="first-page-with-high-limit"),
        pytest.param(10, 10, 0, id="page-num-too-high-no-results"),
    ],
)
def test_get_contexts_pagination(
    dbsession: OrmSession,
    create_schedule: Callable[..., Schedule],
    create_worker: Callable[..., Worker],
    skip: int,
    limit: int,
    expected_results: int,
):
    """Test that get_contexts pagination works correctly"""
    # Create schedules and workers with contexts
    create_schedule(name="schedule1", context="context1")
    create_schedule(name="schedule2", context="context2")
    create_worker(name="worker1", contexts={"context3": None, "context4": None})
    create_worker(name="worker2", contexts={"context5": None, "context6": None})

    # Test first page
    result = get_contexts(dbsession, skip=skip, limit=limit)
    assert result.nb_records == 6
    assert len(result.contexts) == expected_results
