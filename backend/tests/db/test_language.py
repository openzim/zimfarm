from collections.abc import Callable

import pytest
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.common.schemas.models import RecipeConfigSchema
from zimfarm_backend.common.schemas.orms import OfflinerDefinitionSchema, OfflinerSchema
from zimfarm_backend.db.exceptions import RecordDoesNotExistError
from zimfarm_backend.db.language import get_language_from_code, get_languages
from zimfarm_backend.db.models import Recipe
from zimfarm_backend.db.recipe import create_recipe_full_schema, get_recipe


def test_get_languages_empty(dbsession: OrmSession):
    """Test getting languages when no recipes exist."""
    results = get_languages(dbsession, skip=0, limit=100)
    assert results.nb_languages == 0
    assert len(results.languages) == 0


@pytest.fixture
def english_recipe(
    dbsession: OrmSession, mwoffliner_definition: OfflinerDefinitionSchema
):
    """Create a test recipe with English language code."""
    recipe = Recipe(
        language_code="eng",
        name="test",
        category="test",
        config={"test": "test"},
        enabled=True,
        tags=["test"],
        periodicity="test",
        notification={"test": "test"},
    )
    recipe.offliner_definition_id = mwoffliner_definition.id
    dbsession.add(recipe)
    dbsession.flush()
    return recipe


def test_get_languages_single(dbsession: OrmSession, english_recipe: Recipe):
    """Test getting languages with a single recipe."""
    results = get_languages(dbsession, skip=0, limit=100)
    assert results.nb_languages == 1
    assert len(results.languages) == 1
    # Check that the returned language is the English recipe
    assert results.languages[0].code == english_recipe.language_code
    # The name should come from pycountry, not the database
    assert results.languages[0].name == "English"


def test_get_languages_pagination(
    dbsession: OrmSession, mwoffliner_definition: OfflinerDefinitionSchema
):
    """Test getting languages with pagination."""
    # Create test recipes with valid language codes
    recipes = [
        Recipe(
            language_code="eng",  # English
            name="test1",
            category="test",
            config={"test": "test"},
            enabled=True,
            tags=["test"],
            periodicity="test",
            notification={"test": "test"},
        ),
        Recipe(
            language_code="fra",  # French
            name="test2",
            category="test",
            config={"test": "test"},
            enabled=True,
            tags=["test"],
            periodicity="test",
            notification={"test": "test"},
        ),
        Recipe(
            language_code="spa",  # Spanish
            name="test3",
            category="test",
            config={"test": "test"},
            enabled=True,
            tags=["test"],
            periodicity="test",
            notification={"test": "test"},
        ),
        Recipe(
            language_code="eng",  # English
            name="test4",
            category="test",
            config={"test": "test"},
            enabled=True,
            tags=["test"],
            periodicity="test",
            notification={"test": "test"},
        ),
        Recipe(
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
    for recipe in recipes:
        recipe.offliner_definition_id = mwoffliner_definition.id
    dbsession.add_all(recipes)
    dbsession.flush()

    results = get_languages(dbsession, skip=0, limit=2)
    assert results.nb_languages == 3
    assert len(results.languages) == 2


def test_get_invalid_languages(
    dbsession: OrmSession, mwoffliner_definition: OfflinerDefinitionSchema
):
    """Test getting languages with invalid codes"""
    recipes = [
        Recipe(
            language_code="en",  # English
            name="test1",
            category="test",
            config={"test": "test"},
            enabled=True,
            tags=["test"],
            periodicity="test",
            notification={"test": "test"},
        ),
        Recipe(
            language_code="fr",  # French
            name="test2",
            category="test",
            config={"test": "test"},
            enabled=True,
            tags=["test"],
            periodicity="test",
            notification={"test": "test"},
        ),
        Recipe(
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
    for recipe in recipes:
        recipe.offliner_definition_id = mwoffliner_definition.id
    dbsession.add_all(recipes)
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
def test_get_recipe_with_invalid_language_from_db(
    dbsession: OrmSession,
    create_recipe_config: Callable[..., RecipeConfigSchema],
    mwoffliner_definition: OfflinerDefinitionSchema,
    mwoffliner: OfflinerSchema,
    code: str,
):
    # Create test recipe with invalid language code
    recipe = Recipe(
        language_code=code,
        name="test1",
        category="test",
        config=create_recipe_config().model_dump(mode="json"),
        enabled=True,
        tags=["test"],
        periodicity="test",
        notification={"test": "test"},
    )
    recipe.offliner_definition_id = mwoffliner_definition.id
    dbsession.add(recipe)
    dbsession.flush()
    # assert we can read recipes with invalid codes from db
    recipe = get_recipe(dbsession, recipe_name="test1")
    assert recipe.language_code == code
    recipe_schema = create_recipe_full_schema(recipe, mwoffliner)
    # for unknown languages, the code and name should be the same
    assert recipe_schema.language.code == code
    assert recipe_schema.language.name == code


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
