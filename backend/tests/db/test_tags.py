from collections.abc import Callable

from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.db.models import Recipe
from zimfarm_backend.db.tags import get_tags


def test_get_tags_empty(dbsession: OrmSession):
    """Test that get_tags returns empty list when no recipes exist"""
    result = get_tags(dbsession, skip=0, limit=10)
    assert result.nb_records == 0
    assert len(result.tags) == 0


def test_get_tags(
    dbsession: OrmSession,
    create_recipe: Callable[..., Recipe],
):
    """Test that get_tags returns tags from recipes"""
    # Create recipes with different tags
    create_recipe(name="recipe1", tags=["tag1", "tag2"])
    create_recipe(name="recipe2", tags=["tag2", "tag3"])
    create_recipe(name="recipe3", tags=["tag3", "tag4"])
    create_recipe(name="recipe4", tags=["tag4", "tag5"])

    result = get_tags(dbsession, skip=0, limit=2)
    assert result.nb_records == 5
    assert len(result.tags) == 2
    assert sorted(result.tags) == ["tag1", "tag2"]
