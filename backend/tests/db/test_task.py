from collections.abc import Callable
from uuid import UUID

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.common import getnow
from zimfarm_backend.common.enums import TaskStatus
from zimfarm_backend.common.schemas.models import FileCreateUpdateSchema
from zimfarm_backend.db.exceptions import (
    RecordAlreadyExistsError,
    RecordDoesNotExistError,
)
from zimfarm_backend.db.models import File, Recipe, RequestedTask, Task, Team, Worker
from zimfarm_backend.db.requested_task import (
    create_requested_task_full_schema,  # pyright: ignore[reportPrivateUsage]
)
from zimfarm_backend.db.tasks import (
    create_or_update_task_file,
    create_task,
    get_task_by_id,
    get_task_by_id_or_none,
    get_tasks,
)


def test_get_task_by_id_or_none(dbsession: OrmSession, task: Task):
    """Test that get_task_by_id_or_none returns the task if it exists"""
    result = get_task_by_id_or_none(dbsession, task.id, accessible_team_ids=None)
    assert result is not None
    assert result.id == task.id


def test_get_task_by_id_or_none_not_found(dbsession: OrmSession):
    """Test that get_task_by_id_or_none returns None if task doesn't exist"""
    result = get_task_by_id_or_none(dbsession, UUID(int=0), accessible_team_ids=None)
    assert result is None


def test_get_task_by_id(dbsession: OrmSession, task: Task):
    """Test that get_task_by_id returns the task if it exists"""
    result = get_task_by_id(dbsession, task.id, accessible_team_ids=None)
    assert result.id == task.id


def test_get_task_by_id_not_found(dbsession: OrmSession):
    """Test that get_task_by_id raises an exception if task doesn't exist"""
    with pytest.raises(RecordDoesNotExistError):
        get_task_by_id(dbsession, UUID(int=0), accessible_team_ids=None)


@pytest.mark.parametrize(
    "skip,limit,status,recipe_name,offliner, expected_nb_records",
    [
        # No filter
        (0, 5, None, None, None, 3),
        # Filter by status
        (0, 5, [TaskStatus.started], None, None, 1),
        (0, 5, [TaskStatus.started, TaskStatus.requested], None, None, 2),
        # Filter by recipe name
        (0, 5, None, "recipe_1", None, 1),
        (0, 5, None, "nonexistent", None, 0),
        # Combined filters
        (0, 5, [TaskStatus.requested], "recipe_1", None, 1),
        # Filter by offliner
        (0, 5, None, None, "ted", 1),
    ],
    ids=[
        "no_filter",
        "filter_status_started",
        "filter_status_started_requested",
        "filter_recipe_name_recipe_1",
        "filter_recipe_name_nonexistent",
        "filter_status_requested_recipe_1",
        "filter_ted_tasks",
    ],
)
def test_get_tasks(
    dbsession: OrmSession,
    create_task: Callable[..., Task],
    skip: int,
    limit: int,
    status: list[TaskStatus] | None,
    recipe_name: str | None,
    offliner: str | None,
    expected_nb_records: int,
):
    """Test that get_tasks returns the correct list of tasks"""

    create_task(recipe_name="recipe_1", status=TaskStatus.requested, offliner="ted")

    create_task(
        recipe_name="recipe_2",
        status=TaskStatus.succeeded,
    )

    create_task(
        recipe_name="recipe_3",
        status=TaskStatus.started,
    )

    result = get_tasks(
        session=dbsession,
        skip=skip,
        limit=limit,
        accessible_team_ids=None,
        status=status,
        recipe_identifier=recipe_name,
        offliner=offliner,
    )
    assert result.nb_records == expected_nb_records
    assert len(result.records) <= limit


@pytest.mark.parametrize(
    "accessible_teams, expected_recipe_names",
    [
        (None, {"wikipedia_fr_all", "wikipedia_en_all"}),
        ("a", {"wikipedia_fr_all"}),
        ("b", {"wikipedia_en_all"}),
        ("ab", {"wikipedia_fr_all", "wikipedia_en_all"}),
        ("", set[str]()),
    ],
    ids=[
        "all-teams",
        "wikimedia-only",
        "openzim-only",
        "both-teams",
        "no-team",
    ],
)
def test_get_tasks_filters_by_accessible_teams(
    dbsession: OrmSession,
    create_team: Callable[..., Team],
    create_recipe: Callable[..., Recipe],
    create_task: Callable[..., Task],
    accessible_teams: str | None,
    expected_recipe_names: set[str],
):
    """Test that get_tasks only returns tasks from accessible teams"""
    team_a = create_team(name="wikimedia")
    team_b = create_team(name="openzim")
    create_recipe(name="wikipedia_fr_all", teams=[team_a])
    create_recipe(name="wikipedia_en_all", teams=[team_b])
    create_task(recipe_name="wikipedia_fr_all")
    create_task(recipe_name="wikipedia_en_all")

    team_by_key = {"a": team_a, "b": team_b}
    if accessible_teams is None:
        accessible_team_ids = None
    else:
        accessible_team_ids = [team_by_key[key].id for key in accessible_teams]

    result = get_tasks(
        session=dbsession,
        skip=0,
        limit=20,
        accessible_team_ids=accessible_team_ids,
    )
    assert {record.recipe_name for record in result.records} == expected_recipe_names


def test_get_task_by_id_filters_by_accessible_teams(
    dbsession: OrmSession,
    create_team: Callable[..., Team],
    create_recipe: Callable[..., Recipe],
    create_task: Callable[..., Task],
):
    """Test that get_task_by_id only returns tasks from accessible teams"""
    team_a = create_team(name="wikimedia")
    team_b = create_team(name="openzim")
    create_recipe(name="wikipedia_fr_all", teams=[team_a])
    create_recipe(name="wikipedia_en_all", teams=[team_b])
    task_a = create_task(recipe_name="wikipedia_fr_all")
    task_b = create_task(recipe_name="wikipedia_en_all")

    # a task from an accessible team is returned
    assert get_task_by_id(dbsession, task_a.id, [team_a.id]).id == task_a.id

    # a task from another team is not accessible
    with pytest.raises(RecordDoesNotExistError):
        get_task_by_id(dbsession, task_b.id, [team_a.id])

    # the same task is accessible when no team filtering is applied
    assert get_task_by_id(dbsession, task_b.id, None).id == task_b.id


def test_create_task(
    dbsession: OrmSession,
    worker: Worker,
    create_requested_task: Callable[..., RequestedTask],
):
    """Test that create_task creates a task correctly"""

    requested_task = create_requested_task_full_schema(
        dbsession, create_requested_task()
    )
    task = create_task(
        session=dbsession,
        requested_task=requested_task,
        worker_id=worker.id,
        accessible_team_ids=None,
    )
    assert task.id == requested_task.id
    assert task.status == requested_task.status
    assert task.requested_by == requested_task.requested_by
    assert task.priority == requested_task.priority
    assert task.original_recipe_name == requested_task.original_recipe_name
    assert task.worker_name == worker.name


def test_create_task_already_exists(
    dbsession: OrmSession,
    worker: Worker,
    create_requested_task: Callable[..., RequestedTask],
):
    """Test that create_task raises an exception if task already exists"""
    requested_task = create_requested_task_full_schema(
        dbsession, create_requested_task()
    )

    create_task(
        session=dbsession,
        requested_task=requested_task,
        worker_id=worker.id,
        accessible_team_ids=None,
    )

    # Try to create the same task again
    with pytest.raises(RecordAlreadyExistsError):
        create_task(
            session=dbsession,
            requested_task=requested_task,
            worker_id=worker.id,
            accessible_team_ids=None,
        )


def test_create_or_update_task_file_create_minimal(dbsession: OrmSession, task: Task):
    """Test creating a new file with minimal required fields"""
    create_or_update_task_file(
        dbsession,
        FileCreateUpdateSchema(
            task_id=task.id,
            name="test_file.zim",
            status="created",
        ),
    )
    dbsession.flush()

    # Verify the file was created
    result = dbsession.execute(
        select(File).where(File.task_id == task.id, File.name == "test_file.zim")
    ).scalar_one()

    assert result.name == "test_file.zim"
    assert result.status == "created"
    assert result.size is None
    assert result.info == {}


def test_create_or_update_task_file_create_with_all_fields(
    dbsession: OrmSession, task: Task
):
    """Test creating a new file with all fields populated"""
    now = getnow()
    create_or_update_task_file(
        dbsession,
        FileCreateUpdateSchema(
            task_id=task.id,
            name="complete_file.zim",
            status="uploaded",
            size=1024000,
            cms_on=now,
            cms_notified=True,
            created_timestamp=now,
            uploaded_timestamp=now,
            failed_timestamp=None,
            check_timestamp=now,
            check_result=0,
            check_filename="complete_file_zimcheck.json",
            info={"custom": "data"},
        ),
    )
    dbsession.flush()

    # Verify all fields were set
    result = dbsession.execute(
        select(File).where(File.task_id == task.id, File.name == "complete_file.zim")
    ).scalar_one()

    assert result.name == "complete_file.zim"
    assert result.status == "uploaded"
    assert result.size == 1024000
    assert result.cms_on == now
    assert result.cms_notified is True
    assert result.created_timestamp == now
    assert result.uploaded_timestamp == now
    assert result.failed_timestamp is None
    assert result.check_timestamp == now
    assert result.check_result == 0
    assert result.check_filename == "complete_file_zimcheck.json"
    assert result.info == {"custom": "data"}


def test_create_or_update_task_file_update_existing(dbsession: OrmSession, task: Task):
    """Test updating an existing file"""
    # Create initial file
    create_or_update_task_file(
        dbsession,
        FileCreateUpdateSchema(
            task_id=task.id,
            name="update_test.zim",
            status="created",
            size=1000,
            info={"version": "1"},
            cms_notified=False,
        ),
    )
    dbsession.flush()

    # Update the file
    create_or_update_task_file(
        dbsession,
        FileCreateUpdateSchema(
            task_id=task.id,
            name="update_test.zim",
            status="uploaded",
            info={"version": "2"},
        ),
    )
    dbsession.flush()

    # Verify the file was updated with unset fields unchanged
    result = dbsession.execute(
        select(File).where(File.task_id == task.id, File.name == "update_test.zim")
    ).scalar_one()

    assert result.cms_notified is False
    assert result.size == 1000
    assert result.status == "uploaded"
    assert result.info == {"version": "2"}
