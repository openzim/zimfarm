import datetime
from collections.abc import Callable
from contextlib import nullcontext as does_not_raise
from copy import deepcopy
from uuid import uuid4

import pytest
from _pytest.python_api import RaisesContext
from faker import Faker
from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.common.enums import (
    RecipeCategory,
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
    Recipe,
    RecipeHistory,
    RequestedTask,
    Task,
    User,
    Worker,
)
from zimfarm_backend.db.offliner_definition import create_offliner_instance
from zimfarm_backend.db.recipe import (
    DEFAULT_RECIPE_DURATION,
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
    recipe = get_recipe_or_none(dbsession, recipe_name="nonexistent")
    assert recipe is None


def test_get_recipe_not_found(dbsession: OrmSession):
    """Test that get_recipe raises an exception if the recipe does not exist"""
    with pytest.raises(RecordDoesNotExistError):
        get_recipe(dbsession, recipe_name="nonexistent")


def test_get_recipe(dbsession: OrmSession, recipe: Recipe):
    """Test that get_recipe returns the recipe if it exists"""
    db_recipe = get_recipe(dbsession, recipe_name=recipe.name)
    assert db_recipe is not None
    assert db_recipe.name == recipe.name


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
    count = count_enabled_recipes(dbsession, recipe_name)
    assert count == expected_count


def test_get_recipe_duration_default(dbsession: OrmSession, worker: Worker):
    """Test that returns default duration when no specific duration exists"""
    duration = get_recipe_duration(dbsession, recipe_name="nonexistent", worker=worker)
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
    duration = get_recipe_duration(dbsession, recipe_name=recipe.name, worker=worker)
    assert duration.value == recipe.durations[0].value
    assert duration.worker_name is not None
    assert duration.worker_name == worker.name
    assert duration.on == recipe.durations[0].on


def test_create_recipe(
    dbsession: OrmSession,
    user: User,
    create_recipe_config: Callable[..., RecipeConfigSchema],
    mwoffliner_definition: OfflinerDefinitionSchema,
):
    """Test that create_recipe creates a recipe with the correct duration"""
    recipe_config = create_recipe_config(cpu=1, memory=2**10, disk=2**10)
    recipe = create_recipe(
        session=dbsession,
        name="test_recipe",
        category=RecipeCategory.other,
        author_id=user.id,
        language=LanguageSchema(code="eng", name="English"),
        config=recipe_config,
        tags=["test"],
        enabled=True,
        notification=None,
        periodicity=RecipePeriodicity.manually,
        offliner_definition=mwoffliner_definition,
        context="test",
    )

    assert recipe.name == "test_recipe"
    assert recipe.category == RecipeCategory.other
    assert recipe.language_code == "eng"
    assert recipe.context == "test"
    assert recipe.config == recipe_config.model_dump(
        mode="json", context={"show_secrets": True}
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


def test_create_duplicate_recipe_with_existing_name(
    dbsession: OrmSession,
    create_recipe_config: Callable[..., RecipeConfigSchema],
    create_user: Callable[..., User],
    mwoffliner_definition: OfflinerDefinitionSchema,
):
    """Test that create_recipe creates a recipe with the correct duration"""
    recipe_config = create_recipe_config(cpu=1, memory=2**10, disk=2**10)
    recipe_name = "test_recipe"
    user = create_user(username="author")
    create_recipe(
        session=dbsession,
        name=recipe_name,
        author_id=user.id,
        category=RecipeCategory.other,
        language=LanguageSchema(code="eng", name="English"),
        config=recipe_config,
        tags=["test"],
        enabled=True,
        notification=None,
        periodicity=RecipePeriodicity.manually,
        offliner_definition=mwoffliner_definition,
    )
    with pytest.raises(RecordAlreadyExistsError):
        create_recipe(
            session=dbsession,
            name=recipe_name,
            author_id=user.id,
            category=RecipeCategory.other,
            language=LanguageSchema(code="eng", name="English"),
            config=recipe_config,
            tags=["test"],
            enabled=True,
            notification=None,
            periodicity=RecipePeriodicity.manually,
            offliner_definition=mwoffliner_definition,
        )


def test_get_all_recipes(dbsession: OrmSession, create_recipe: Callable[..., Recipe]):
    """Test that get_all_recipes returns all recipes"""
    recipe = create_recipe()
    results = get_all_recipes(dbsession)
    assert results.nb_records == 1
    assert results.recipes[0].name == recipe.name


def test_update_recipe(
    dbsession: OrmSession,
    user: User,
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
            author_id=user.id,
            recipe_name=old_recipe.name,
            new_recipe_config=new_recipe_config,
            name=old_recipe.name + "_updated",
            offliner_definition=mwoffliner_definition,
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
    delete_recipe(dbsession, recipe_name=recipe.name)
    assert get_recipe_or_none(dbsession, recipe_name=recipe.name) is None
    # assert that there is no recipe history entry
    assert (
        count_from_stmt(
            dbsession,
            select(RecipeHistory).where(RecipeHistory.recipe_id == recipe.id),
        )
        == 0
    )


def test_delete_recipe_not_found(dbsession: OrmSession):
    """Test that delete_recipe raises an exception if the recipe does not exist"""
    with pytest.raises(RecordDoesNotExistError):
        delete_recipe(dbsession, recipe_name="nonexistent")


@pytest.mark.parametrize(
    "name,lang,categories,tags,expected_count",
    [
        pytest.param(None, None, None, None, 30, id="all"),
        pytest.param("wiki", ["eng"], None, None, 10, id="wiki_eng"),
        pytest.param("wiki", ["eng", "fra"], None, None, 20, id="wiki_eng_fra"),
        pytest.param(
            "recipe",
            None,
            [RecipeCategory.wikipedia],
            None,
            0,
            id="recipe_wikipedia",
        ),
        pytest.param(None, ["eng"], None, ["important"], 10, id="eng_important"),
        pytest.param("nonexistent", None, None, None, 0, id="nonexistent"),
        pytest.param(
            "recipe",
            ["eng"],
            [RecipeCategory.other],
            ["test"],
            10,
            id="recipe_eng_other_test",
        ),
    ],
)
def test_get_recipes(
    dbsession: OrmSession,
    create_recipe: Callable[..., Recipe],
    create_requested_task: Callable[..., RequestedTask],
    create_task: Callable[..., Task],
    name: str | None,
    lang: list[str] | None,
    categories: list[RecipeCategory] | None,
    tags: list[str] | None,
    expected_count: int,
):
    """Test that get_recipes works correctly with combined filters"""
    for i in range(10):
        recipe = create_recipe(
            name=f"wiki_eng_{i}",
            category=RecipeCategory.wikipedia,
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
            category=RecipeCategory.wikipedia,
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
            category=RecipeCategory.other,
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
        name=name,
        lang=lang,
        categories=categories,
        tags=tags,
    )
    assert results.nb_records == expected_count
    assert len(results.recipes) <= limit
    for result_recipe in results.recipes:
        assert result_recipe.config is not None
        assert result_recipe.most_recent_task is not None


def test_update_recipe_duration_no_tasks(
    dbsession: OrmSession, create_recipe: Callable[..., Recipe]
):
    """Test that update_recipe_duration does nothing when no matching tasks exist"""
    recipe = create_recipe(name="test_recipe")

    update_recipe_duration(dbsession, recipe_name=recipe.name)

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

    update_recipe_duration(dbsession, recipe_name=recipe.name)

    # Expire the recipe to force a reload of the recipe
    dbsession.expire(recipe)
    updated_recipe = get_recipe(dbsession, recipe_name=recipe.name)

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

    update_recipe_duration(dbsession, recipe_name=recipe.name)

    # Expire the recipe to force a reload of the recipe
    dbsession.expire(recipe)
    updated_recipe = get_recipe(dbsession, recipe_name=recipe.name)

    # Verify no new durations were created (only the default remains)
    assert len(updated_recipe.durations) == 1
    assert updated_recipe.durations[0].default is True


def test_update_recipe_duration_multiple_workers(
    dbsession: OrmSession,
    create_recipe: Callable[..., Recipe],
    create_task: Callable[..., Task],
    create_worker: Callable[..., Worker],
):
    """Test that update_recipe_duration handles multiple workers correctly"""
    recipe = create_recipe(name="test_recipe")
    worker1 = create_worker(name="worker1")
    worker2 = create_worker(name="worker2")

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

    update_recipe_duration(dbsession, recipe_name=recipe.name)

    dbsession.expire(recipe)
    updated_recipe = get_recipe(dbsession, recipe_name=recipe.name)

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
        dbsession, recipe_name=recipe.name, history_id=uuid4()
    )
    assert history_entry is None


def test_get_recipe_history_entry_or_none(dbsession: OrmSession, recipe: Recipe):
    history_entry = get_recipe_history_entry_or_none(
        dbsession,
        recipe_name=recipe.name,
        history_id=recipe.history_entries[0].id,
    )
    assert history_entry is not None


def test_get_recipe_history_entry(dbsession: OrmSession, recipe: Recipe):
    with pytest.raises(RecordDoesNotExistError):
        get_recipe_history_entry(
            dbsession,
            recipe_name=recipe.name,
            history_id=uuid4(),
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
    create_user: Callable[..., User],
    *,
    archived: bool,
    new_archive_status: bool,
    expected: RaisesContext[Exception],
):
    user = create_user()
    with expected:
        recipe = create_recipe(archived=archived)
        toggle_archive_status(
            dbsession,
            recipe_name=recipe.name,
            archived=new_archive_status,
            actor_id=user.id,
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
    create_user: Callable[..., User],
    recipe_names: list[str],
    expected: RaisesContext[Exception],
):
    user = create_user()
    create_recipe(name="testrecipe", archived=True)

    with expected:
        restore_recipes(dbsession, recipe_names=recipe_names, actor_id=user.id)


def test_revert_recipe_archived_recipe(
    dbsession: OrmSession,
    create_recipe: Callable[..., Recipe],
    user: User,
):
    """Test that reverting an archived recipe raises an error"""
    recipe = create_recipe(name="archived_recipe", archived=True)
    history_id = recipe.history_entries[0].id

    with pytest.raises(
        RecordDoesNotExistError,
    ):
        revert_recipe(
            dbsession,
            recipe_name="archived_recipe",
            history_id=history_id,
            author_id=user.id,
        )


def test_revert_recipe_no_offliner_definition_version(
    dbsession: OrmSession,
    create_recipe: Callable[..., Recipe],
    user: User,
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
            recipe_name="test_recipe",
            history_id=history_entry.id,
            author_id=user.id,
        )


def test_revert_recipe_all_fields(
    dbsession: OrmSession,
    create_recipe: Callable[..., Recipe],
    recipe_config: RecipeConfigSchema,
    mwoffliner_definition: OfflinerDefinitionSchema,
    mwoffliner: OfflinerSchema,
    user: User,
    data_gen: Faker,
):
    """Test that all recipe fields are properly reverted"""
    initial_notification: dict[str, dict[str, list[str]]] = {
        "requested": {"mailgun": ["test@example.com"]},
        "started": {"mailgun": []},
        "ended": {"mailgun": []},
    }
    recipe = create_recipe(
        name="test_recipe",
        enabled=True,
        tags=["tag1", "tag2"],
        category="wikipedia",
        periodicity="monthly",
        context="initial context",
        recipe_config=recipe_config,
        notification=initial_notification,
    )
    initial_history_id = recipe.history_entries[0].id
    initial_config = deepcopy(recipe.config)
    initial_tags = deepcopy(recipe.tags)
    initial_category = recipe.category
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
        author_id=user.id,
        recipe_name="test_recipe",
        new_recipe_config=new_recipe_config,
        offliner_definition=mwoffliner_definition,
        tags=["tag3", "tag4"],
        category=RecipeCategory.other,
        periodicity=RecipePeriodicity.quarterly,
        context="updated context",
        enabled=False,
        comment="Update all fields",
        notification=RecipeNotificationSchema(
            requested=EventNotificationSchema(
                mailgun=["updated@example.com", "another@example.com"]
            )
        ),
    )

    updated_recipe = get_recipe(dbsession, recipe_name="test_recipe")

    assert updated_recipe.config != initial_config
    assert updated_recipe.tags != initial_tags
    assert updated_recipe.category != initial_category
    assert updated_recipe.periodicity != initial_periodicity
    assert updated_recipe.context != initial_context
    assert updated_recipe.enabled != initial_enabled
    assert updated_recipe.notification != initial_notification

    reverted_recipe = revert_recipe(
        dbsession,
        recipe_name="test_recipe",
        history_id=initial_history_id,
        author_id=user.id,
    )

    assert reverted_recipe.config == initial_config
    assert reverted_recipe.tags == initial_tags
    assert reverted_recipe.category == initial_category
    assert reverted_recipe.periodicity == initial_periodicity
    assert reverted_recipe.context == initial_context
    assert reverted_recipe.enabled == initial_enabled
    assert reverted_recipe.notification == initial_notification
