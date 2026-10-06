import datetime
from collections.abc import Callable
from contextlib import nullcontext as does_not_raise
from copy import deepcopy
from uuid import uuid4

import pytest
from _pytest.raises import RaisesExc
from faker import Faker
from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.common.enums import (
    RecipePeriodicity,
    TaskStatus,
    WarehousePath,
)
from zimfarm_backend.common.schemas.models import (
    EventNotificationSchema,
    RecipeConfigSchema,
    RecipeNotificationSchema,
)
from zimfarm_backend.common.schemas.orms import (
    LanguageSchema,
    OfflinerDefinitionSchema,
    OfflinerSchema,
)
from zimfarm_backend.db import count_from_stmt
from zimfarm_backend.db.exceptions import (
    RecordAlreadyExistsError,
    RecordDoesNotExistError,
)
from zimfarm_backend.db.models import (
    Account,
    Recipe,
    RecipeHistory,
    RequestedTask,
    Task,
    Team,
    Worker,
)
from zimfarm_backend.db.offliner_definition import create_offliner_instance
from zimfarm_backend.db.recipe import (
    DEFAULT_RECIPE_DURATION,
    RecipeCreateSchema,
    RecipeUpdateSchema,
    count_enabled_recipes,
    create_recipe,
    create_recipe_full_schema,
    delete_recipe,
    get_all_recipes,
    get_recipe,
    get_recipe_duration,
    get_recipe_history_entry,
    get_recipe_history_entry_or_none,
    get_recipe_or_none,
    get_recipes,
    restore_recipes,
    revert_recipe,
    toggle_archive_status,
    update_recipe,
    update_recipe_duration,
)


def test_get_recipe_or_none(dbsession: OrmSession):
    """Test that get_recipe_or_none returns None if the recipe does not exist"""
    recipe = get_recipe_or_none(dbsession, "nonexistent", accessible_team_ids=None)
    assert recipe is None


def test_get_recipe_not_found(dbsession: OrmSession):
    """Test that get_recipe raises an exception if the recipe does not exist"""
    with pytest.raises(RecordDoesNotExistError):
        get_recipe(dbsession, "nonexistent", accessible_team_ids=None)


def test_get_recipe(dbsession: OrmSession, recipe: Recipe):
    """Test that get_recipe returns the recipe if it exists"""
    db_recipe = get_recipe(dbsession, str(recipe.id), accessible_team_ids=None)
    assert db_recipe is not None
    assert db_recipe.name == recipe.name
    assert db_recipe.id == recipe.id


@pytest.mark.parametrize(
    "recipe_name, expected_count",
    [(["nonexistent"], 0), (["testrecipe"], 1), (["testrecipe", "nonexistent"], 1)],
)
def test_count_enabled_recipes(
    dbsession: OrmSession,
    recipe: Recipe,  # noqa: ARG001
    recipe_name: list[str],
    expected_count: int,
):
    """Test that count_enabled_recipes returns the correct count"""
    count = count_enabled_recipes(dbsession, recipe_name, accessible_team_ids=None)
    assert count == expected_count


def test_get_recipe_duration_default(dbsession: OrmSession, worker: Worker):
    """Test that returns default duration when no specific duration exists"""
    duration = get_recipe_duration(
        dbsession,
        recipe_identifier="nonexistent",
        worker_name=worker.name,
        accessible_team_ids=None,
    )
    assert duration.value > 0
    assert duration.worker_name is None
    assert isinstance(duration.on, datetime.datetime)


def test_get_recipe_duration_with_worker(
    dbsession: OrmSession,
    create_recipe: Callable[..., Recipe],
    worker: Worker,
):
    """Returns worker-specific duration when recipe exists"""
    recipe = create_recipe(worker=worker)
    duration = get_recipe_duration(
        dbsession,
        recipe_identifier=str(recipe.id),
        worker_name=worker.name,
        accessible_team_ids=None,
    )
    assert duration.value == recipe.durations[0].value
    assert duration.worker_name is not None
    assert duration.worker_name == worker.name
    assert duration.on == recipe.durations[0].on


def test_create_recipe(
    dbsession: OrmSession,
    account: Account,
    create_recipe_config: Callable[..., RecipeConfigSchema],
    mwoffliner_definition: OfflinerDefinitionSchema,
    team: Team,
):
    """Test that create_recipe creates a recipe with the correct duration"""
    recipe_config = create_recipe_config(cpu=1, memory=2**10, disk=2**10)
    recipe = create_recipe(
        session=dbsession,
        author_id=account.id,
        payload=RecipeCreateSchema(
            name="test_recipe",
            language=LanguageSchema(code="eng", name="English"),
            config=recipe_config,
            tags=["test"],
            enabled=True,
            notification=None,
            periodicity=RecipePeriodicity.manually,
            context="test",
            teams=[team.name],
        ),
        offliner_definition=mwoffliner_definition,
        accessible_team_ids=None,
    )

    assert recipe.name == "test_recipe"
    assert recipe.language_code == "eng"
    assert recipe.context == "test"
    assert recipe.config == recipe_config.model_dump(
        mode="json", context={"show_secrets": True}, exclude_none=True
    )
    assert recipe.tags == ["test"]
    assert recipe.enabled
    assert recipe.notification is None
    assert recipe.periodicity == RecipePeriodicity.manually
    assert len(recipe.durations) == 1
    assert recipe.durations[0].value == DEFAULT_RECIPE_DURATION.value
    assert recipe.durations[0].on == DEFAULT_RECIPE_DURATION.on
    assert recipe.durations[0].worker is None
    assert recipe.durations[0].default
    assert len(recipe.history_entries) == 1
    assert {entry["name"] for entry in recipe.history_entries[0].teams} == {team.name}


def test_create_duplicate_recipe_with_existing_name(
    dbsession: OrmSession,
    create_recipe_config: Callable[..., RecipeConfigSchema],
    create_account: Callable[..., Account],
    mwoffliner_definition: OfflinerDefinitionSchema,
    team: Team,
):
    """Test that create_recipe creates a recipe with the correct duration"""
    recipe_config = create_recipe_config(cpu=1, memory=2**10, disk=2**10)
    recipe_name = "test_recipe"
    account = create_account(username="author")
    payload = RecipeCreateSchema(
        name=recipe_name,
        language=LanguageSchema(code="eng", name="English"),
        config=recipe_config,
        tags=["test"],
        enabled=True,
        notification=None,
        periodicity=RecipePeriodicity.manually,
        teams=[team.name],
    )
    create_recipe(
        session=dbsession,
        author_id=account.id,
        payload=payload,
        offliner_definition=mwoffliner_definition,
        accessible_team_ids=None,
    )
    with pytest.raises(RecordAlreadyExistsError):
        create_recipe(
            session=dbsession,
            author_id=account.id,
            payload=payload,
            offliner_definition=mwoffliner_definition,
            accessible_team_ids=None,
        )


@pytest.mark.parametrize(
    "initial_teams,updated_teams,expected_teams",
    [
        pytest.param(["wikimedia"], ["openzim"], {"openzim"}, id="replace-team"),
        pytest.param(
            ["wikimedia"],
            ["wikimedia", "openzim"],
            {"wikimedia", "openzim"},
            id="add-team",
        ),
        pytest.param(
            ["wikimedia", "openzim"],
            ["openzim"],
            {"openzim"},
            id="remove-team",
        ),
    ],
)
def test_update_recipe_teams(
    dbsession: OrmSession,
    account: Account,
    create_team: Callable[..., Team],
    create_recipe: Callable[..., Recipe],
    mwoffliner_definition: OfflinerDefinitionSchema,
    initial_teams: list[str],
    updated_teams: list[str],
    expected_teams: set[str],
):
    """Test that update_recipe replaces teams and records them in history"""
    teams = {name: create_team(name=name) for name in ("wikimedia", "openzim")}
    recipe = create_recipe(
        name="wikipedia_fr_all", teams=[teams[name] for name in initial_teams]
    )
    assert {team_recipe.team.name for team_recipe in recipe.teams} == set(initial_teams)

    update_recipe(
        dbsession,
        author_id=account.id,
        recipe_identifier=recipe.name,
        accessible_team_ids=None,
        payload=RecipeUpdateSchema(
            offliner_definition=mwoffliner_definition,
            teams=updated_teams,
        ),
    )

    updated_recipe = get_recipe(dbsession, recipe.name, accessible_team_ids=None)
    assert {
        team_recipe.team.name for team_recipe in updated_recipe.teams
    } == expected_teams
    assert expected_teams in [
        {entry["name"] for entry in history_entry.teams}
        for history_entry in updated_recipe.history_entries
    ]


def test_get_all_recipes(dbsession: OrmSession, create_recipe: Callable[..., Recipe]):
    """Test that get_all_recipes returns all recipes"""
    recipe = create_recipe()
    results = get_all_recipes(dbsession, accessible_team_ids=None)
    assert results.nb_records == 1
    assert results.records[0].name == recipe.name


@pytest.mark.parametrize(
    "accessible_teams,expected_names",
    [
        pytest.param(None, {"wikipedia_fr_all", "wikipedia_en_all"}, id="all"),
        pytest.param(["a"], {"wikipedia_fr_all"}, id="wikimedia"),
        pytest.param(["b"], {"wikipedia_en_all"}, id="openzim"),
        pytest.param(
            ["a", "b"],
            {"wikipedia_fr_all", "wikipedia_en_all"},
            id="wikimedia-and-openzim",
        ),
        pytest.param([], set[str](), id="none"),
    ],
)
def test_get_recipes_filters_by_accessible_teams(
    dbsession: OrmSession,
    create_team: Callable[..., Team],
    create_recipe: Callable[..., Recipe],
    accessible_teams: list[str] | None,
    expected_names: set[str],
):
    """Test that get_recipes only returns recipes from accessible teams"""
    team_a = create_team(name="wikimedia", is_private=True)
    team_b = create_team(name="openzim", is_private=True)
    create_recipe(name="wikipedia_fr_all", teams=[team_a])
    create_recipe(name="wikipedia_en_all", teams=[team_b])

    accessible_team_ids = (
        None
        if accessible_teams is None
        else [{"a": team_a.id, "b": team_b.id}[key] for key in accessible_teams]
    )

    results = get_recipes(
        dbsession,
        skip=0,
        limit=100,
        accessible_team_ids=accessible_team_ids,
    )
    assert {record.name for record in results.records} == expected_names


@pytest.mark.parametrize(
    "accessible_teams,expected_names",
    [
        pytest.param(None, {"wikipedia_fr_all", "wikipedia_en_all"}, id="all"),
        pytest.param(["a"], {"wikipedia_fr_all"}, id="wikimedia"),
        pytest.param(["b"], {"wikipedia_en_all"}, id="openzim"),
        pytest.param([], set[str](), id="none"),
    ],
)
def test_get_all_recipes_filters_by_accessible_teams(
    dbsession: OrmSession,
    create_team: Callable[..., Team],
    create_recipe: Callable[..., Recipe],
    accessible_teams: list[str] | None,
    expected_names: set[str],
):
    """Test that get_all_recipes only returns recipes from accessible teams"""
    team_a = create_team(name="wikimedia", is_private=True)
    team_b = create_team(name="openzim", is_private=True)
    create_recipe(name="wikipedia_fr_all", teams=[team_a])
    create_recipe(name="wikipedia_en_all", teams=[team_b])

    accessible_team_ids = (
        None
        if accessible_teams is None
        else [{"a": team_a.id, "b": team_b.id}[key] for key in accessible_teams]
    )

    results = get_all_recipes(dbsession, accessible_team_ids=accessible_team_ids)
    assert {record.name for record in results.records} == expected_names


@pytest.mark.parametrize(
    "accessible_teams,is_accessible",
    [
        pytest.param(None, True, id="all"),
        pytest.param(["b"], True, id="openzim"),
        pytest.param(["a"], False, id="wikimedia"),
        pytest.param([], False, id="none"),
    ],
)
def test_get_recipe_or_none_filters_by_accessible_teams(
    dbsession: OrmSession,
    create_team: Callable[..., Team],
    create_recipe: Callable[..., Recipe],
    accessible_teams: list[str] | None,
    *,
    is_accessible: bool,
):
    """Test that get_recipe_or_none/get_recipe only resolve accessible recipes"""
    team_a = create_team(name="wikimedia", is_private=True)
    team_b = create_team(name="openzim", is_private=True)
    create_recipe(name="wikipedia_fr_all", teams=[team_a])
    create_recipe(name="wikipedia_en_all", teams=[team_b])

    accessible_team_ids = (
        None
        if accessible_teams is None
        else [{"a": team_a.id, "b": team_b.id}[key] for key in accessible_teams]
    )

    result = get_recipe_or_none(dbsession, "wikipedia_en_all", accessible_team_ids)
    if is_accessible:
        assert result is not None
        assert result.name == "wikipedia_en_all"
        assert get_recipe(dbsession, "wikipedia_en_all", accessible_team_ids).name == (
            "wikipedia_en_all"
        )
    else:
        assert result is None
        with pytest.raises(RecordDoesNotExistError):
            get_recipe(dbsession, "wikipedia_en_all", accessible_team_ids)


def test_update_recipe(
    dbsession: OrmSession,
    account: Account,
    create_recipe: Callable[..., Recipe],
    create_recipe_config: Callable[..., RecipeConfigSchema],
    mwoffliner: OfflinerSchema,
    mwoffliner_definition: OfflinerDefinitionSchema,
):
    """Test that update_recipe updates a recipe"""
    old_recipe = create_recipe_full_schema(create_recipe(), mwoffliner)
    new_recipe_config = create_recipe_config(
        cpu=old_recipe.config.resources.cpu * 2,
        memory=old_recipe.config.resources.memory * 2,
        disk=old_recipe.config.resources.disk * 2,
    )
    updated_recipe = create_recipe_full_schema(
        update_recipe(
            dbsession,
            author_id=account.id,
            recipe_identifier=str(old_recipe.id),
            accessible_team_ids=None,
            payload=RecipeUpdateSchema(
                offliner_definition=mwoffliner_definition,
                config=new_recipe_config,
                name=old_recipe.name + "_updated",
            ),
        ),
        mwoffliner,
    )
    assert updated_recipe.config.resources.cpu != old_recipe.config.resources.cpu
    assert updated_recipe.config.resources.memory != old_recipe.config.resources.memory
    assert updated_recipe.config.resources.disk != old_recipe.config.resources.disk
    assert updated_recipe.name == old_recipe.name + "_updated"


def test_delete_recipe(dbsession: OrmSession, create_recipe: Callable[..., Recipe]):
    """Test that delete_recipe deletes a recipe"""
    recipe = create_recipe()
    recipe_id = recipe.id
    delete_recipe(dbsession, str(recipe.id), accessible_team_ids=None)
    assert (
        get_recipe_or_none(dbsession, str(recipe_id), accessible_team_ids=None) is None
    )
    # assert that there is no recipe history entry
    assert (
        count_from_stmt(
            dbsession,
            select(RecipeHistory).where(RecipeHistory.recipe_id == recipe_id),
        )
        == 0
    )


def test_delete_recipe_not_found(dbsession: OrmSession):
    """Test that delete_recipe raises an exception if the recipe does not exist"""
    with pytest.raises(RecordDoesNotExistError):
        delete_recipe(dbsession, "nonexistent", accessible_team_ids=None)


@pytest.mark.parametrize(
    "name,lang,tags,expected_count",
    [
        pytest.param(None, None, None, 30, id="all"),
        pytest.param("wiki", ["eng"], None, 10, id="wiki_eng"),
        pytest.param("wiki", ["eng", "fra"], None, 20, id="wiki_eng_fra"),
        pytest.param("nonexistent", None, None, 0, id="nonexistent"),
    ],
)
def test_get_recipes(
    dbsession: OrmSession,
    create_recipe: Callable[..., Recipe],
    create_requested_task: Callable[..., RequestedTask],
    create_task: Callable[..., Task],
    name: str | None,
    lang: list[str] | None,
    tags: list[str] | None,
    expected_count: int,
):
    """Test that get_recipes works correctly with combined filters"""
    for i in range(10):
        recipe = create_recipe(
            name=f"wiki_eng_{i}",
            language=LanguageSchema(code="eng", name="English"),
            tags=["important"],
        )
        requested_task = create_requested_task(recipe_name=recipe.name)
        task = create_task(requested_task=requested_task)
        recipe.most_recent_task = task
        recipe.similarity_data = ["hello"]
        dbsession.add(recipe)
        dbsession.flush()

    for i in range(10):
        recipe = create_recipe(
            name=f"wiki_fra_{i}",
            language=LanguageSchema(code="fra", name="French"),
            tags=["important"],
        )
        requested_task = create_requested_task(recipe_name=recipe.name)
        task = create_task(requested_task=requested_task)
        recipe.most_recent_task = task
        recipe.similarity_data = ["world"]
        dbsession.add(recipe)
        dbsession.flush()

    for i in range(10):
        recipe = create_recipe(
            name=f"other_recipe_{i}",
            language=LanguageSchema(code="eng", name="English"),
            tags=["test"],
        )
        requested_task = create_requested_task(recipe_name=recipe.name)
        task = create_task(requested_task=requested_task)
        recipe.most_recent_task = task
        recipe.similarity_data = ["foo", "bar"]
        dbsession.add(recipe)
        dbsession.flush()

    limit = 5
    results = get_recipes(
        dbsession,
        skip=0,
        limit=limit,
        accessible_team_ids=None,
        name=name,
        lang=lang,
        tags=tags,
    )
    assert results.nb_records == expected_count
    assert len(results.records) <= limit
    for result_recipe in results.records:
        assert result_recipe.config is not None
        assert result_recipe.most_recent_task is not None


def test_update_recipe_duration_no_tasks(
    dbsession: OrmSession, create_recipe: Callable[..., Recipe]
):
    """Test that update_recipe_duration does nothing when no matching tasks exist"""
    recipe = create_recipe(name="test_recipe")

    update_recipe_duration(
        dbsession, recipe_identifier=recipe.name, accessible_team_ids=None
    )

    assert len(recipe.durations) == 1
    assert recipe.durations[0].default is True


def test_update_recipe_duration_with_completed_tasks(
    dbsession: OrmSession,
    create_recipe: Callable[..., Recipe],
    create_task: Callable[..., Task],
    worker: Worker,
):
    """Test that update_recipe_duration creates worker-specific durations"""
    recipe = create_recipe(name="test_recipe")

    # Create a task that completed successfully
    started_time = datetime.datetime(2023, 1, 1, 10, 0, 0)
    completed_time = datetime.datetime(2023, 1, 1, 12, 0, 0)  # 2 hours later

    task = create_task(
        recipe_name=recipe.name,
        status=TaskStatus.scraper_completed,
        worker=worker,
    )

    # Set up the task with proper timestamps and exit code
    task.timestamp = [
        (TaskStatus.started.value, started_time),
        (TaskStatus.scraper_completed.value, completed_time),
    ]
    task.container = {"exit_code": 0}
    dbsession.add(task)
    dbsession.flush()

    update_recipe_duration(
        dbsession, recipe_identifier=str(recipe.id), accessible_team_ids=None
    )

    # Expire the recipe to force a reload of the recipe
    dbsession.expire(recipe)
    updated_recipe = get_recipe(dbsession, recipe.name, accessible_team_ids=None)

    assert len(updated_recipe.durations) == 2  # Default + worker-specific

    # Find the worker-specific duration
    worker_duration = next(
        (d for d in updated_recipe.durations if d.worker_id == worker.id), None
    )

    assert worker_duration is not None
    assert worker_duration.default is False
    assert worker_duration.on == completed_time


def test_update_recipe_duration_with_failed_tasks(
    dbsession: OrmSession,
    create_recipe: Callable[..., Recipe],
    create_task: Callable[..., Task],
    worker: Worker,
):
    """Test that update_recipe_duration ignores tasks with non-zero exit codes"""
    recipe = create_recipe(name="test_recipe")

    # Create a task that failed (exit_code != 0)
    started_time = datetime.datetime(2023, 1, 1, 10, 0, 0)
    completed_time = datetime.datetime(2023, 1, 1, 12, 0, 0)

    task = create_task(
        recipe_name=recipe.name,
        status=TaskStatus.scraper_completed,
        worker=worker,
    )

    # Set up the task with proper timestamps but failed exit code
    task.timestamp = [
        (TaskStatus.started.value, started_time),
        (TaskStatus.scraper_completed.value, completed_time),
    ]
    task.container = {"exit_code": 1}  # Failed task
    dbsession.add(task)
    dbsession.flush()

    update_recipe_duration(
        dbsession, recipe_identifier=recipe.name, accessible_team_ids=None
    )

    # Expire the recipe to force a reload of the recipe
    dbsession.expire(recipe)
    updated_recipe = get_recipe(dbsession, recipe.name, accessible_team_ids=None)

    # Verify no new durations were created (only the default remains)
    assert len(updated_recipe.durations) == 1
    assert updated_recipe.durations[0].default is True


def test_update_recipe_duration_multiple_workers(
    dbsession: OrmSession,
    create_recipe: Callable[..., Recipe],
    create_task: Callable[..., Task],
    create_worker: Callable[..., Worker],
    create_account: Callable[..., Account],
):
    """Test that update_recipe_duration handles multiple workers correctly"""
    recipe = create_recipe(name="test_recipe")
    worker1 = create_worker(account=create_account(), name="worker1")
    worker2 = create_worker(account=create_account(), name="worker2")

    # Create tasks for both workers
    task1 = create_task(
        recipe_name=recipe.name,
        status=TaskStatus.scraper_completed,
        worker=worker1,
    )
    task1.timestamp = [
        (TaskStatus.started.value, datetime.datetime(2023, 1, 1, 10, 0, 0)),
        (
            TaskStatus.scraper_completed.value,
            datetime.datetime(2023, 1, 1, 11, 0, 0),
        ),  # 1 hour
    ]
    task1.container = {"exit_code": 0}

    task2 = create_task(
        recipe_name=recipe.name,
        status=TaskStatus.scraper_completed,
        worker=worker2,
    )
    task2.timestamp = [
        (TaskStatus.started.value, datetime.datetime(2023, 1, 1, 10, 0, 0)),
        (
            TaskStatus.scraper_completed.value,
            datetime.datetime(2023, 1, 1, 12, 0, 0),
        ),  # 2 hours
    ]
    task2.container = {"exit_code": 0}

    dbsession.add_all([task1, task2])
    dbsession.flush()

    update_recipe_duration(
        dbsession, recipe_identifier=recipe.name, accessible_team_ids=None
    )

    dbsession.expire(recipe)
    updated_recipe = get_recipe(dbsession, recipe.name, accessible_team_ids=None)

    assert len(updated_recipe.durations) == 3  # Default + 2 worker-specific

    worker1_duration = next(
        (d for d in updated_recipe.durations if d.worker_id == worker1.id), None
    )
    assert worker1_duration is not None

    worker2_duration = next(
        (d for d in updated_recipe.durations if d.worker_id == worker2.id), None
    )
    assert worker2_duration is not None


def test_get_recipe_history_entry_or_none_not_found(
    dbsession: OrmSession, recipe: Recipe
):
    history_entry = get_recipe_history_entry_or_none(
        dbsession,
        recipe_identifier=recipe.name,
        history_id=uuid4(),
        accessible_team_ids=None,
    )
    assert history_entry is None


def test_get_recipe_history_entry_or_none(dbsession: OrmSession, recipe: Recipe):
    history_entry = get_recipe_history_entry_or_none(
        dbsession,
        recipe_identifier=recipe.name,
        history_id=recipe.history_entries[0].id,
        accessible_team_ids=None,
    )
    assert history_entry is not None


def test_get_recipe_history_entry(dbsession: OrmSession, recipe: Recipe):
    with pytest.raises(RecordDoesNotExistError):
        get_recipe_history_entry(
            dbsession,
            recipe_identifier=recipe.name,
            history_id=uuid4(),
            accessible_team_ids=None,
        )


@pytest.mark.parametrize(
    "archived,new_archive_status,expected",
    [
        pytest.param(False, True, does_not_raise()),
        pytest.param(False, False, pytest.raises(RecordAlreadyExistsError)),
        pytest.param(True, True, pytest.raises(RecordAlreadyExistsError)),
        pytest.param(True, False, does_not_raise()),
    ],
)
def test_toggle_recipe_archive_status(
    dbsession: OrmSession,
    create_recipe: Callable[..., Recipe],
    create_account: Callable[..., Account],
    *,
    archived: bool,
    new_archive_status: bool,
    expected: RaisesExc[Exception],
):
    account = create_account()
    with expected:
        recipe = create_recipe(archived=archived)
        toggle_archive_status(
            dbsession,
            recipe_identifier=recipe.name,
            archived=new_archive_status,
            actor_id=account.id,
            accessible_team_ids=None,
        )


@pytest.mark.parametrize(
    "recipe_names,expected",
    [
        pytest.param(["nonexistent"], pytest.raises(RecordDoesNotExistError)),
        pytest.param(["testrecipe"], does_not_raise()),
        pytest.param(
            ["testrecipe", "nonexistent"], pytest.raises(RecordDoesNotExistError)
        ),
    ],
)
def test_restore_recipes(
    dbsession: OrmSession,
    create_recipe: Callable[..., Recipe],
    create_account: Callable[..., Account],
    recipe_names: list[str],
    expected: RaisesExc[Exception],
):
    account = create_account()
    create_recipe(name="testrecipe", archived=True)

    with expected:
        restore_recipes(
            dbsession,
            recipe_identifiers=recipe_names,
            actor_id=account.id,
            accessible_team_ids=None,
        )


def test_revert_recipe_archived_recipe(
    dbsession: OrmSession,
    create_recipe: Callable[..., Recipe],
    account: Account,
):
    """Test that reverting an archived recipe raises an error"""
    recipe = create_recipe(name="archived_recipe", archived=True)
    history_id = recipe.history_entries[0].id

    with pytest.raises(
        RecordDoesNotExistError,
    ):
        revert_recipe(
            dbsession,
            recipe_identifier="archived_recipe",
            history_id=history_id,
            author_id=account.id,
            accessible_team_ids=None,
        )


def test_revert_recipe_no_offliner_definition_version(
    dbsession: OrmSession,
    create_recipe: Callable[..., Recipe],
    account: Account,
):
    """Test that reverting to history with no offliner definition version
    raises error"""
    recipe = create_recipe(name="test_recipe")
    history_entry = recipe.history_entries[0]

    history_entry.offliner_definition_version = None
    dbsession.add(history_entry)

    with pytest.raises(
        ValueError,
    ):
        revert_recipe(
            dbsession,
            recipe_identifier="test_recipe",
            history_id=history_entry.id,
            author_id=account.id,
            accessible_team_ids=None,
        )


def test_revert_recipe_all_fields(
    dbsession: OrmSession,
    create_recipe: Callable[..., Recipe],
    recipe_config: RecipeConfigSchema,
    mwoffliner_definition: OfflinerDefinitionSchema,
    mwoffliner: OfflinerSchema,
    account: Account,
    data_gen: Faker,
):
    """Test that all recipe fields are properly reverted"""
    initial_notification: dict[str, dict[str, list[str]]] = {
        "requested": {"email": ["test@example.com"]},
        "started": {"email": []},
        "ended": {"email": []},
    }
    recipe = create_recipe(
        name="test_recipe",
        enabled=True,
        tags=["tag1", "tag2"],
        periodicity="monthly",
        context="initial context",
        recipe_config=recipe_config,
        notification=initial_notification,
    )
    initial_history_id = recipe.history_entries[0].id
    initial_config = deepcopy(recipe.config)
    initial_tags = deepcopy(recipe.tags)
    initial_periodicity = recipe.periodicity
    initial_context = recipe.context
    initial_enabled = recipe.enabled

    new_recipe_config = RecipeConfigSchema.model_validate(
        {
            **recipe_config.model_dump(
                mode="json",
                exclude={"offliner"},
                context={"show_secrets": True},
            ),
            "image": {
                "name": mwoffliner.docker_image_name,
                "tag": "1.17",
            },
            "warehouse_path": WarehousePath.libretexts,
            "offliner": create_offliner_instance(
                offliner=mwoffliner,
                offliner_definition=mwoffliner_definition,
                data={
                    "offliner_id": mwoffliner_definition.offliner,
                    "mwUrl": data_gen.uri(),
                    "adminEmail": data_gen.email(),
                    "mwPassword": "new-password",
                },
            ),
        }
    )
    update_recipe(
        dbsession,
        author_id=account.id,
        recipe_identifier="test_recipe",
        accessible_team_ids=None,
        payload=RecipeUpdateSchema(
            offliner_definition=mwoffliner_definition,
            config=new_recipe_config,
            tags=["tag3", "tag4"],
            periodicity=RecipePeriodicity.quarterly,
            context="updated context",
            enabled=False,
            comment="Update all fields",
            notification=RecipeNotificationSchema(
                requested=EventNotificationSchema(
                    email=["updated@example.com", "another@example.com"]
                )
            ),
        ),
    )

    updated_recipe = get_recipe(dbsession, "test_recipe", accessible_team_ids=None)

    assert updated_recipe.config != initial_config
    assert updated_recipe.tags != initial_tags
    assert updated_recipe.periodicity != initial_periodicity
    assert updated_recipe.context != initial_context
    assert updated_recipe.enabled != initial_enabled
    assert updated_recipe.notification != initial_notification

    reverted_recipe = revert_recipe(
        dbsession,
        recipe_identifier="test_recipe",
        history_id=initial_history_id,
        author_id=account.id,
        accessible_team_ids=None,
    )

    assert reverted_recipe.config == initial_config
    assert reverted_recipe.tags == initial_tags
    assert reverted_recipe.periodicity == initial_periodicity
    assert reverted_recipe.context == initial_context
    assert reverted_recipe.enabled == initial_enabled
    assert reverted_recipe.notification == initial_notification
