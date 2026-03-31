from collections.abc import Callable

from pytest import MonkeyPatch
from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.background_tasks import history_cleanup as history_cleanup_module
from zimfarm_backend.background_tasks.history_cleanup import history_cleanup
from zimfarm_backend.db import count_from_stmt
from zimfarm_backend.db.models import Recipe, Task


def test_history_cleanup_recipe_with_few_tasks(
    dbsession: OrmSession,
    create_recipe: Callable[..., Recipe],
    create_task: Callable[..., Task],
    monkeypatch: MonkeyPatch,
):
    """Test that history_cleanup doesn't delete tasks when count is below threshold"""
    recipe = create_recipe()

    monkeypatch.setattr(history_cleanup_module, "HISTORY_TASK_PER_RECIPE", 10)
    # Create 5 tasks (below the default threshold of 10)
    for _ in range(5):
        create_task(recipe_name=recipe.name)
    history_cleanup(dbsession)

    # No tasks should be deleted
    assert count_from_stmt(dbsession, select(Task.id)) == 5


def test_history_cleanup_recipe_with_many_tasks(
    dbsession: OrmSession,
    create_recipe: Callable[..., Recipe],
    create_task: Callable[..., Task],
    monkeypatch: MonkeyPatch,
):
    """Test that history_cleanup deletes old tasks when count exceeds threshold"""
    monkeypatch.setattr(history_cleanup_module, "HISTORY_TASK_PER_RECIPE", 10)
    recipe = create_recipe()

    # Create 15 tasks (above the default threshold of 10)
    for _ in range(15):
        create_task(recipe_name=recipe.name)

    history_cleanup(dbsession)

    assert count_from_stmt(dbsession, select(Task.id)) == 10


def test_history_cleanup_multiple_recipes(
    dbsession: OrmSession,
    create_recipe: Callable[..., Recipe],
    create_task: Callable[..., Task],
    monkeypatch: MonkeyPatch,
):
    """Test that history_cleanup handles multiple recipes correctly"""
    monkeypatch.setattr(history_cleanup_module, "HISTORY_TASK_PER_RECIPE", 10)
    recipe1 = create_recipe(name="recipe_1")
    recipe2 = create_recipe(name="recipe_2")
    recipe3 = create_recipe(name="recipe_3")

    # Recipe 1: 15 tasks (should be cleaned)
    for _ in range(15):
        create_task(recipe_name=recipe1.name)

    # Recipe 2: 5 tasks (should not be cleaned)
    for _ in range(5):
        create_task(recipe_name=recipe2.name)

    # Recipe 3: 12 tasks (should be cleaned)
    for _ in range(12):
        create_task(recipe_name=recipe3.name)

    history_cleanup(dbsession)

    # Check each recipe
    assert (
        count_from_stmt(dbsession, select(Task.id).where(Task.recipe_id == recipe1.id))
        == 10
    )

    assert (
        count_from_stmt(dbsession, select(Task.id).where(Task.recipe_id == recipe2.id))
        == 5
    )

    assert (
        count_from_stmt(dbsession, select(Task.id).where(Task.recipe_id == recipe3.id))
        == 10
    )
