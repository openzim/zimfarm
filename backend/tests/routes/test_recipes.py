from collections.abc import Callable
from http import HTTPStatus
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.api.token import generate_access_token
from zimfarm_backend.common import getnow
from zimfarm_backend.common.enums import RecipeCategory, RecipePeriodicity
from zimfarm_backend.common.roles import RoleEnum
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
from zimfarm_backend.db.models import Account, Recipe, RequestedTask, Task
from zimfarm_backend.db.offliner_definition import create_offliner_definition_schema
from zimfarm_backend.db.recipe import get_recipe, update_recipe


@pytest.mark.parametrize(
    "query_string,expected_count",
    [
        pytest.param("", 10, id="all"),
        pytest.param("&name=wiki&lang=eng", 10, id="wiki_eng"),
        pytest.param("&name=wiki&lang=fra", 0, id="wiki_fra"),
        pytest.param("&name=recipe&category=wikipedia", 0, id="recipe_wikipedia"),
        pytest.param("&name=recipe&lang=eng&tag=important", 0, id="eng_important"),
        pytest.param("&name=nonexistent", 0, id="nonexistent"),
        pytest.param(
            "&name=recipe&lang=eng&category=other&tag=test",
            0,
            id="recipe_eng_other_test",
        ),
        pytest.param(
            "&name=wiki&lang=eng&category=wikipedia&tag=important",
            10,
            id="wiki_eng_important",
        ),
    ],
)
def test_get_recipes(
    client: TestClient,
    dbsession: OrmSession,
    create_account: Callable[..., Account],
    create_recipe: Callable[..., Recipe],
    create_requested_task: Callable[..., RequestedTask],
    create_task: Callable[..., Task],
    query_string: str,
    expected_count: int,
):
    account = create_account(permission=RoleEnum.PROCESSOR)
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )

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
        recipe.similarity_data = ["hello", "world"]
        dbsession.add(recipe)
        dbsession.flush()

    url = "/v2/recipes?skip=0&limit=5"
    response = client.get(
        url + query_string,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert "items" in data
    assert "meta" in data
    assert "count" in data["meta"]
    assert "skip" in data["meta"]
    assert data["meta"]["count"] == expected_count
    assert len(data["items"]) <= 5


@pytest.mark.parametrize(
    "permission,expected_status_code",
    [
        pytest.param(RoleEnum.ADMIN, HTTPStatus.OK, id="admin"),
        pytest.param(RoleEnum.PROCESSOR, HTTPStatus.FORBIDDEN, id="processor"),
    ],
)
def test_get_archived_recipes(
    client: TestClient,
    create_account: Callable[..., Account],
    create_recipe: Callable[..., Recipe],
    permission: RoleEnum,
    expected_status_code: HTTPStatus,
):
    account = create_account(permission=permission)
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )
    create_recipe(name="test_recipe", archived=True)

    response = client.get(
        "/v2/recipes?skip=0&limit=1&archived=true",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == expected_status_code


def test_get_similar_recipes(
    client: TestClient,
    dbsession: OrmSession,
    create_account: Callable[..., Account],
    create_recipe: Callable[..., Recipe],
    create_requested_task: Callable[..., RequestedTask],
    create_task: Callable[..., Task],
):
    account = create_account(permission=RoleEnum.PROCESSOR)
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )

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
        recipe.similarity_data = ["hello", "world"]
        dbsession.add(recipe)
        dbsession.flush()

    url = "/v2/recipes/wiki_eng_0/similar?skip=0&limit=5"
    response = client.get(
        url,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert "items" in data
    assert "meta" in data
    assert "count" in data["meta"]
    assert "skip" in data["meta"]
    for item in data["items"]:
        assert item["name"] != "wiki_eng_0"
    assert data["meta"]["count"] == 9  # recipe itself is not included
    assert len(data["items"]) <= 5


@pytest.mark.parametrize(
    "payload,expected_status_code",
    [
        pytest.param(
            {
                "name": "test_recipe",
                "category": RecipeCategory.wikipedia.value,
                "language": "eng",
                "tags": ["important"],
                "config": {
                    "warehouse_path": "/videos",
                    "image": {
                        "name": "openzim/mwoffliner",
                        "tag": "latest",
                    },
                    "resources": {
                        "cpu": 4,
                        "memory": 2**30,
                        "disk": 2**30,
                    },
                    "offliner": {
                        "mwUrl": "https://en.wikipedia.org",
                        "adminEmail": "test@kiwix.org",
                        "mwPassword": "test-password",
                    },
                    "platform": "wikimedia",
                    "monitor": True,
                },
                "enabled": True,
                "periodicity": RecipePeriodicity.manually.value,
                "version": "initial",
            },
            HTTPStatus.UNPROCESSABLE_ENTITY,
            id="invalid-config-missing-offliner-id",
        ),
        pytest.param(
            {
                "name": "test_recipe",
                "category": RecipeCategory.wikipedia.value,
                "language": "eng",
                "tags": ["important"],
                "config": {
                    "warehouse_path": "/videos",
                    "image": {
                        "name": "openzim/mwoffliner",
                        "tag": "latest",
                    },
                    "resources": {
                        "cpu": 4,
                        "memory": 2**30,
                        "disk": 2**30,
                    },
                    "offliner": {
                        "offliner_id": "mwoffliner",
                        "mwUrl": "https://en.wikipedia.org",
                        "adminEmail": "test@kiwix.org",
                        "mwPassword": "test-password",
                        "extra_key": "extra",
                    },
                    "platform": "wikimedia",
                    "monitor": True,
                },
                "enabled": True,
                "periodicity": RecipePeriodicity.manually.value,
                "version": "initial",
            },
            HTTPStatus.UNPROCESSABLE_ENTITY,
            id="invalid-config-extra-keys",
        ),
        pytest.param(
            {
                "name": "test_recipe",
                "category": RecipeCategory.wikipedia.value,
                "language": "eng",
                "tags": ["important"],
                "config": {
                    "warehouse_path": "/videos",
                    "image": {
                        "name": "openzim/mwoffliner",
                        "tag": "latest",
                    },
                    "resources": {
                        "cpu": 4,
                        "memory": 2**30,
                        "disk": 2**30,
                    },
                    "offliner": {
                        "offliner_id": "mwoffliner",
                        "mwUrl": "https://en.wikipedia.org",
                        "adminEmail": "test@kiwix.org",
                        "mwPassword": "test-password",
                    },
                    "platform": "wikimedia",
                    "monitor": True,
                },
                "enabled": True,
                "periodicity": RecipePeriodicity.manually.value,
                "version": "notfound",
            },
            HTTPStatus.NOT_FOUND,
            id="valid-config-offliner-version-does-not-exist",
        ),
        pytest.param(
            {
                "name": "test_recipe",
                "category": RecipeCategory.wikipedia.value,
                "language": "eng",
                "tags": ["important"],
                "config": {
                    "warehouse_path": "/videos",
                    "image": {
                        "name": "openzim/mwoffliner",
                        "tag": "latest",
                    },
                    "resources": {
                        "cpu": 4,
                        "memory": 2**30,
                        "disk": 2**30,
                    },
                    "offliner": {
                        "offliner_id": "mwoffliner",
                        "mwUrl": "https://en.wikipedia.org",
                        "adminEmail": "test@kiwix.org",
                        "mwPassword": "test-password",
                    },
                    "platform": "wikimedia",
                    "monitor": True,
                },
                "enabled": True,
                "periodicity": RecipePeriodicity.manually.value,
                "context": "test",
                "version": "initial",
            },
            HTTPStatus.OK,
            id="valid-config",
        ),
    ],
)
def test_create_recipe(
    client: TestClient,
    create_account: Callable[..., Account],
    mwoffliner_definition: OfflinerDefinitionSchema,  # noqa: ARG001
    payload: dict[str, Any],
    expected_status_code: HTTPStatus,
):
    """Test that create_recipe raises Unprocessable Entity with invalid config"""
    account = create_account(permission=RoleEnum.ADMIN)
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )

    response = client.post(
        "/v2/recipes",
        headers={"Authorization": f"Bearer {access_token}"},
        json=payload,
    )
    assert response.status_code == expected_status_code


@pytest.mark.parametrize(
    "permission,expected_status_code",
    [
        pytest.param(RoleEnum.ADMIN, HTTPStatus.OK, id="admin"),
        pytest.param(RoleEnum.PROCESSOR, HTTPStatus.FORBIDDEN, id="processor"),
    ],
)
def test_create_recipe_with_permssions(
    client: TestClient,
    dbsession: OrmSession,
    create_account: Callable[..., Account],
    create_recipe_config: Callable[..., RecipeConfigSchema],
    mwoffliner_definition: OfflinerDefinitionSchema,
    permission: RoleEnum,
    expected_status_code: HTTPStatus,
):
    """Test that create_recipe raises ForbiddenError without permission"""
    account = create_account(permission=permission)
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )

    recipe_config = create_recipe_config()

    response = client.post(
        "/v2/recipes",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "name": "test_recipe",
            "category": RecipeCategory.wikipedia.value,
            "language": "eng",
            "tags": ["important"],
            "config": recipe_config.model_dump(
                mode="json", context={"show_secrets": True}
            ),
            "enabled": True,
            "periodicity": RecipePeriodicity.manually.value,
            "version": mwoffliner_definition.version,
            "context": "test",
        },
    )
    assert response.status_code == expected_status_code
    if response.status_code == HTTPStatus.OK:
        # assert top-level scalar attributes of the recipe with the payload
        recipe = get_recipe(dbsession, recipe_name="test_recipe")
        assert recipe.language_code == "eng"
        assert recipe.tags == ["important"]
        assert recipe.enabled is True
        assert recipe.context == "test"
        assert recipe.periodicity == RecipePeriodicity.manually.value
        assert recipe.category == RecipeCategory.wikipedia.value


@pytest.mark.parametrize(
    "recipe_name,expected_status_code",
    [
        pytest.param("test_recipe", HTTPStatus.OK, id="valid-recipe-name"),
        pytest.param(
            "test-recipe/",
            HTTPStatus.UNPROCESSABLE_ENTITY,
            id="slash-in-recipe-name",
        ),
        pytest.param("none", HTTPStatus.UNPROCESSABLE_ENTITY, id="none-as-recipe-name"),
        pytest.param(
            "testRecipe", HTTPStatus.UNPROCESSABLE_ENTITY, id="uppercase-char"
        ),
    ],
)
def test_recipe_name(
    client: TestClient,
    create_account: Callable[..., Account],
    create_recipe_config: Callable[..., RecipeConfigSchema],
    mwoffliner_definition: OfflinerDefinitionSchema,
    recipe_name: str,
    expected_status_code: int,
):
    """Test that create_recipe raises Unprocessable entity with invalid name"""
    account = create_account(permission=RoleEnum.ADMIN)
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )

    recipe_config = create_recipe_config()

    response = client.post(
        "/v2/recipes",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "name": recipe_name,
            "category": RecipeCategory.wikipedia.value,
            "language": "eng",
            "tags": ["important"],
            "config": recipe_config.model_dump(
                mode="json", context={"show_secrets": True}
            ),
            "enabled": True,
            "periodicity": RecipePeriodicity.manually.value,
            "version": mwoffliner_definition.version,
        },
    )
    assert response.status_code == expected_status_code


@pytest.mark.parametrize(
    "permission,hide_secrets",
    [
        pytest.param(RoleEnum.ADMIN, False, id="admin-no-hide-secrets"),
        pytest.param(RoleEnum.ADMIN, True, id="admin-hide-secrets"),
    ],
)
def test_get_recipe(
    client: TestClient,
    dbsession: OrmSession,
    create_account: Callable[..., Account],
    create_recipe: Callable[..., Recipe],
    permission: RoleEnum,
    *,
    hide_secrets: bool,
):
    account = create_account(permission=permission)
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )

    recipe = create_recipe(name="test_recipe")
    dbsession.add(recipe)
    dbsession.flush()

    _hide_secrets = "true" if hide_secrets else "false"
    response = client.get(
        f"/v2/recipes/{recipe.name}?hide_secrets={_hide_secrets}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    data = response.json()
    assert "config" in data
    assert "offliner" in data["config"]
    assert "mwPassword" in data["config"]["offliner"]

    if hide_secrets:
        for char in data["config"]["offliner"]["mwPassword"]:
            assert char == "*"
    else:
        assert data["config"]["offliner"]["mwPassword"] == "test-password"


def test_get_obsolete_recipe(
    client: TestClient,
    dbsession: OrmSession,
    create_account: Callable[..., Account],
    create_recipe: Callable[..., Recipe],
    create_recipe_config: Callable[..., RecipeConfigSchema],
    mwoffliner: OfflinerSchema,  # noqa: ARG001 needed for side effect
    mwoffliner_definition: OfflinerDefinitionSchema,  # noqa: ARG001 needed for side effect
):
    account = create_account(permission=RoleEnum.ADMIN)
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )

    recipe_config = create_recipe_config()
    raw_recipe_config = recipe_config.model_dump(
        mode="json", context={"show_secrets": True}
    )
    raw_recipe_config["offliner"]["mwUrl"] = None  # Unset mandatory field
    raw_recipe_config["offliner"]["oldFlag"] = "anyValue"  # Set unknown field
    recipe = create_recipe(name="test_recipe", raw_recipe_config=raw_recipe_config)
    dbsession.add(recipe)
    dbsession.flush()

    response = client.get(
        f"/v2/recipes/{recipe.name}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == HTTPStatus.OK
    recipe_data = response.json()
    assert "config" in recipe_data
    assert "offliner" in recipe_data["config"]
    assert "mwUrl" in recipe_data["config"]["offliner"]
    assert recipe_data["config"]["offliner"]["mwUrl"] is None
    assert "oldFlag" in recipe_data["config"]["offliner"]
    assert recipe_data["config"]["offliner"]["oldFlag"] == "anyValue"


def test_patch_obsolete_recipe(
    client: TestClient,
    dbsession: OrmSession,
    create_account: Callable[..., Account],
    create_recipe: Callable[..., Recipe],
    create_recipe_config: Callable[..., RecipeConfigSchema],
    mwoffliner: OfflinerSchema,  # noqa: ARG001 needed for side effect
    mwoffliner_definition: OfflinerDefinitionSchema,  # noqa: ARG001 needed for side effect
):
    account = create_account(permission=RoleEnum.ADMIN)
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )

    recipe_config = create_recipe_config()
    raw_recipe_config = recipe_config.model_dump(
        mode="json", context={"show_secrets": True}
    )
    raw_recipe_config["offliner"]["mwUrl"] = None  # Unset mandatory field
    raw_recipe_config["offliner"]["oldFlag"] = "anyValue"  # Set unknown field
    recipe = create_recipe(name="test_recipe", raw_recipe_config=raw_recipe_config)
    dbsession.add(recipe)
    dbsession.flush()

    response = client.patch(
        f"/v2/recipes/{recipe.name}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "flags": {"mwUrl": "http://fr.wikipedia.org", "adminEmail": "bob@acme.com"},
        },
    )

    assert response.status_code == HTTPStatus.OK
    recipe_data = response.json()
    assert "config" in recipe_data
    assert "offliner" in recipe_data["config"]
    assert "mwUrl" in recipe_data["config"]["offliner"]
    assert recipe_data["config"]["offliner"]["mwUrl"] == "http://fr.wikipedia.org/"
    assert "oldFlag" not in recipe_data["config"]["offliner"]


def test_update_recipe_forbidden(
    client: TestClient,
    create_account: Callable[..., Account],
):
    """Test that update_recipe raises ForbiddenError without permission"""
    account = create_account(permission=RoleEnum.PROCESSOR)
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )

    response = client.patch(
        "/v2/recipes/nonexistent",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "name": "test_recipe",
            "category": RecipeCategory.wikipedia.value,
        },
    )
    assert response.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.parametrize(
    "payload,expected_status_code",
    [
        pytest.param(
            {
                "offliner": "youtube",
                "flags": {"mwUrl": "http://fr.wikipedia.org"},
            },
            HTTPStatus.BAD_REQUEST,
            id="different_offliner_version_unset",
        ),
        pytest.param(
            {"offliner": "youtube", "flags": {}, "version": "initial"},
            HTTPStatus.BAD_REQUEST,
            id="different_offliner_flags_empty",
        ),
        pytest.param(
            {"offliner": "youtube", "version": "initial"},
            HTTPStatus.BAD_REQUEST,
            id="different_offliner_flags_unset",
        ),
        pytest.param(
            {
                "offliner": "youtube",
                "flags": {"mwUrl": "http://fr.wikipedia.org"},
                "version": "initial",
            },
            HTTPStatus.BAD_REQUEST,
            id="different_offliner_image_unset",
        ),
        pytest.param(
            {
                "offliner": "youtube",
                "flags": {"mwUrl": "http://fr.wikipedia.org"},
                "version": "doesnotexist",
                "image": {"name": "openzim/mwoffliner", "tag": "latest"},
            },
            HTTPStatus.NOT_FOUND,
            id="different_offliner_but_definition_does_not_exist",
        ),
        pytest.param(
            {
                "image": {"name": "openzim/phet", "tag": "latest"},
            },
            HTTPStatus.BAD_REQUEST,
            id="same_offliner_different_image",
        ),
        pytest.param(
            {
                "offliner": "ted",
                "flags": {"mwUrl": "http://fr.wikipedia.org"},
                "image": {"name": "openzim/ted", "tag": "latest"},
                "version": "initial",
            },
            HTTPStatus.UNPROCESSABLE_ENTITY,
            id="different_offliner_wrong_flags",
        ),
        pytest.param(
            {
                "offliner": "ted",
                "flags": {"name": "ted-talks_eng_football", "topics": "football"},
                "image": {"name": "openzim/ted", "tag": "latest"},
                "version": "initial",
            },
            HTTPStatus.OK,
            id="different_offliner_good_update",
        ),
        pytest.param(
            {
                "image": {"name": "openzim/mwoffliner", "tag": "1.12.2"},
            },
            HTTPStatus.OK,
            id="good_mw_offliner_image_update",
        ),
        pytest.param(
            {},
            HTTPStatus.BAD_REQUEST,
            id="no_changes",
        ),
    ],
)
def test_update_recipe(
    client: TestClient,
    dbsession: OrmSession,
    create_account: Callable[..., Account],
    create_recipe: Callable[..., Recipe],
    mwoffliner: OfflinerSchema,  # noqa: ARG001 needed for side effect
    mwoffliner_definition: OfflinerDefinitionSchema,  # noqa: ARG001 needed for side effect
    tedoffliner_definition: OfflinerDefinitionSchema,  # noqa: ARG001 needed for side effect
    ted_offliner: OfflinerSchema,  # noqa: ARG001 needed for side effect
    payload: dict[str, Any],
    expected_status_code: HTTPStatus,
):
    account = create_account(permission=RoleEnum.ADMIN)
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )

    recipe = create_recipe(name="test_recipe")
    dbsession.add(recipe)
    dbsession.flush()

    response = client.patch(
        f"/v2/recipes/{recipe.name}",
        headers={"Authorization": f"Bearer {access_token}"},
        json=payload,
    )
    assert response.status_code == expected_status_code


@pytest.mark.parametrize(
    "permission,expected_status_code",
    [
        pytest.param(RoleEnum.ADMIN, HTTPStatus.NO_CONTENT, id="admin"),
        pytest.param(RoleEnum.PROCESSOR, HTTPStatus.FORBIDDEN, id="processor"),
    ],
)
def test_delete_recipe(
    client: TestClient,
    dbsession: OrmSession,
    create_account: Callable[..., Account],
    create_recipe: Callable[..., Recipe],
    permission: RoleEnum,
    expected_status_code: HTTPStatus,
):
    account = create_account(permission=permission)
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )

    recipe = create_recipe(name="test_recipe")
    dbsession.add(recipe)
    dbsession.flush()

    response = client.delete(
        f"/v2/recipes/{recipe.name}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == expected_status_code


@patch("zimfarm_backend.api.routes.recipes.logic.get_recipe_image_tags")
def test_get_recipe_image_names(
    mock_get_tags: MagicMock,
    client: TestClient,
    dbsession: OrmSession,
    create_recipe: Callable[..., Recipe],
):
    mock_get_tags.return_value = ["latest", "1.0.0", "1.0.1"]
    recipe = create_recipe(name="test_recipe")
    dbsession.add(recipe)
    dbsession.flush()

    response = client.get(
        f"/v2/recipes/{recipe.name}/image-names?hub_name=openzim/mwoffliner",
    )
    mock_get_tags.assert_called_once_with("openzim/mwoffliner")

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert "items" in data
    assert data["items"] == ["latest", "1.0.0", "1.0.1"]


@pytest.mark.parametrize(
    "new_language_code,expected_validity_status",
    [
        pytest.param("invalid", False, id="invalid-language-code"),
        pytest.param("eng", True, id="valid-language-code"),
    ],
)
def test_clone_recipe(
    client: TestClient,
    dbsession: OrmSession,
    create_account: Callable[..., Account],
    create_recipe: Callable[..., Recipe],
    new_language_code: str,
    *,
    expected_validity_status: bool,
):
    account = create_account(permission=RoleEnum.ADMIN)
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )

    recipe = create_recipe(name="test_recipe")
    recipe.language_code = new_language_code
    dbsession.add(recipe)
    dbsession.flush()

    response = client.post(
        f"/v2/recipes/{recipe.name}/clone",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"name": "test_recipe_clone"},
    )
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert "id" in data
    assert data["id"] is not None
    assert str(data["id"]) != str(recipe.id)

    new_recipe = get_recipe(dbsession, recipe_name="test_recipe_clone")
    assert new_recipe.is_valid == expected_validity_status


@pytest.mark.parametrize(
    "permission,new_language_code,expected_status_code",
    [
        pytest.param(
            RoleEnum.ADMIN,
            "invalid",
            HTTPStatus.UNPROCESSABLE_ENTITY,
            id="invalid-language-code-admin",
        ),
        pytest.param(
            RoleEnum.ADMIN,
            "eng",
            HTTPStatus.OK,
            id="valid-language-code-admin",
        ),
        pytest.param(
            RoleEnum.PROCESSOR,
            "eng",
            HTTPStatus.FORBIDDEN,
            id="valid-language-code-processor",
        ),
    ],
)
def test_validate_recipe(
    client: TestClient,
    dbsession: OrmSession,
    create_account: Callable[..., Account],
    create_recipe: Callable[..., Recipe],
    permission: RoleEnum,
    new_language_code: str,
    *,
    expected_status_code: HTTPStatus,
):
    account = create_account(permission=permission)
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )
    recipe = create_recipe(name="test_recipe")
    # set the new language code in the db
    recipe.language_code = new_language_code
    dbsession.add(recipe)
    dbsession.flush()

    response = client.get(
        f"/v2/recipes/{recipe.name}/validate",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == expected_status_code


def test_create_duplicate_recipe(
    client: TestClient,
    dbsession: OrmSession,
    create_account: Callable[..., Account],
    create_recipe: Callable[..., Recipe],
    create_recipe_config: Callable[..., RecipeConfigSchema],
):
    recipe_config = create_recipe_config()
    recipe = create_recipe(name="test_recipe", recipe_config=recipe_config)
    dbsession.add(recipe)
    dbsession.flush()

    account = create_account(permission=RoleEnum.ADMIN)
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )

    response = client.post(
        "/v2/recipes",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "name": "test_recipe",
            "category": RecipeCategory.wikipedia.value,
            "language": "eng",
            "tags": ["important"],
            "config": recipe_config.model_dump(
                mode="json", context={"show_secrets": True}
            ),
            "enabled": True,
            "periodicity": RecipePeriodicity.manually.value,
            "version": "initial",
        },
    )
    assert response.status_code == HTTPStatus.CONFLICT


def test_clone_existing_recipe_with_name_unchanged(
    client: TestClient,
    dbsession: OrmSession,
    create_account: Callable[..., Account],
    create_recipe: Callable[..., Recipe],
    create_recipe_config: Callable[..., RecipeConfigSchema],
):
    account = create_account(permission=RoleEnum.ADMIN)
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )

    recipe_config = create_recipe_config()
    recipe = create_recipe(name="test_recipe", recipe_config=recipe_config)
    dbsession.add(recipe)
    dbsession.flush()

    response = client.post(
        f"/v2/recipes/{recipe.name}/clone",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"name": "test_recipe"},
    )
    assert response.status_code == HTTPStatus.CONFLICT


def test_update_existing_recipe_with_existing_name(
    client: TestClient,
    dbsession: OrmSession,
    create_account: Callable[..., Account],
    create_recipe: Callable[..., Recipe],
    create_recipe_config: Callable[..., RecipeConfigSchema],
):
    """Test that updating a recipe name with another existing recipe name fails"""
    account = create_account(permission=RoleEnum.ADMIN)
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )

    recipe_config = create_recipe_config()
    recipes = [
        create_recipe(name=f"test_recipe_{i}", recipe_config=recipe_config)
        for i in range(3)
    ]
    dbsession.add_all(recipes)
    dbsession.flush()

    # attempt to update recipe_1 with the name of recipe_2
    response = client.patch(
        "/v2/recipes/test_recipe_1",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "name": "test_recipe_2",
        },
    )
    assert response.status_code == HTTPStatus.CONFLICT


@pytest.mark.parametrize(
    "payload,check_attrs,expected_status_code",
    [
        pytest.param(
            {
                "platform": "shamela",
                "resources": {
                    "cpu": 1,
                    "memory": 1024,
                    "disk": 1024,
                },
                "monitor": True,
                "artifacts_globs": ["**/*.json"],
            },
            {"platform", "resources", "monitor", "artifacts_globs"},
            HTTPStatus.OK,
            id="platform-resources-monitor-artifacts_globs",
        ),
        pytest.param(
            {
                "platform": None,
                "monitor": False,
                "artifacts_globs": [],
            },
            {"platform", "monitor", "artifacts_globs"},
            HTTPStatus.OK,
            id="platform-monitor-artifacts_globs",
        ),
        pytest.param(
            {
                "platform": "",
                "monitor": False,
                "artifacts_globs": [],
            },
            {"platform", "monitor", "artifacts_globs"},
            HTTPStatus.UNPROCESSABLE_ENTITY,
            id="invalid-platform-empty-string",
        ),
        pytest.param(
            {
                "platform": None,
                "monitor": False,
                "artifacts_globs": None,
            },
            {"platform", "monitor", "artifacts_globs"},
            HTTPStatus.UNPROCESSABLE_ENTITY,
            # artifact_globs should not be None but platform can be None at config level
            id="platform-none-artifacts_globs-none",
        ),
        pytest.param(
            {
                "resources": {
                    "cpu": 1,
                    "memory": 1024,
                    "disk": 1024,
                },
            },
            {"resources"},
            HTTPStatus.OK,
            id="resources-only-update",
        ),
        pytest.param(
            {
                "resources": None,
            },
            {"resources"},
            HTTPStatus.UNPROCESSABLE_ENTITY,
            # resources explicitly set to None but cannot be None at config level
            id="resources-none",
        ),
        pytest.param(
            {
                "monitor": None,
            },
            {"monitor"},
            HTTPStatus.UNPROCESSABLE_ENTITY,
            # monitor explicitly set to None but cannot be None at config level
            id="monitor-none",
        ),
        pytest.param(
            {
                "artifacts_globs": None,
            },
            {"artifacts_globs"},
            HTTPStatus.UNPROCESSABLE_ENTITY,
            # artifacts_globs should not be None but can be None at config level
            id="artifacts_globs-none",
        ),
    ],
)
def test_update_recipe_config_top_level_attributes(
    client: TestClient,
    dbsession: OrmSession,
    create_account: Callable[..., Account],
    create_recipe: Callable[..., Recipe],
    payload: dict[str, Any],
    check_attrs: set[str],
    expected_status_code: HTTPStatus,
):
    account = create_account(permission=RoleEnum.ADMIN)
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )

    recipe = create_recipe(name="test_recipe")
    dbsession.add(recipe)
    dbsession.flush()

    response = client.patch(
        f"/v2/recipes/{recipe.name}",
        headers={"Authorization": f"Bearer {access_token}"},
        json=payload,
    )
    assert response.status_code == expected_status_code
    if response.status_code == HTTPStatus.OK:
        data = response.json()
        for attr in check_attrs:
            if isinstance(data["config"][attr], dict):
                # check that the values we set are in the nested dict as
                # response sometimes contains extra fields that are not in
                # the request payload. e.g resources response contains
                # cap_add, cap_drop and shm which are not in the request payload
                for key in payload[attr]:
                    assert data["config"][attr][key] == payload[attr][key]
            else:
                assert data["config"][attr] == payload[attr]


@pytest.mark.parametrize(
    "permission,expected_status_code",
    [
        pytest.param(RoleEnum.ADMIN, HTTPStatus.OK, id="admin"),
        pytest.param(RoleEnum.PROCESSOR, HTTPStatus.FORBIDDEN, id="processor"),
    ],
)
def test_get_recipe_history(
    client: TestClient,
    dbsession: OrmSession,
    create_account: Callable[..., Account],
    create_recipe: Callable[..., Recipe],
    permission: RoleEnum,
    expected_status_code: HTTPStatus,
):
    account = create_account(permission=permission)
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )

    recipe = create_recipe(name="test_recipe")
    dbsession.add(recipe)
    dbsession.flush()

    response = client.get(
        f"/v2/recipes/{recipe.name}/history?limit=10&skip=0",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == expected_status_code


@pytest.mark.parametrize(
    "query_string,expected_count",
    [
        pytest.param("", 10, id="all"),
        pytest.param("limit=5&skip=0", 5, id="first-page"),
        pytest.param("limit=5&skip=5", 5, id="second-page"),
        pytest.param("limit=10&skip=10", 0, id="third-page"),
    ],
)
def test_get_recipe_history_pagination(
    client: TestClient,
    dbsession: OrmSession,
    create_account: Callable[..., Account],
    create_recipe: Callable[..., Recipe],
    query_string: str,
    expected_count: int,
):
    account = create_account(username="test", permission=RoleEnum.ADMIN)
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )
    recipe = create_recipe(
        name="test_recipe",
        category=RecipeCategory.wikipedia,
        language=LanguageSchema(code="eng", name="English"),
        tags=["important"],
    )

    #  When we created a recipe, we created 1 history entry
    for i in range(9):
        update_recipe(
            session=dbsession,
            author_id=account.id,
            recipe_name=recipe.name,
            comment=f"test_comment_{i}",
            tags=[*recipe.tags, f"test_tag_{i}"],
            offliner_definition=create_offliner_definition_schema(
                recipe.offliner_definition
            ),
        )

    url = f"/v2/recipes/{recipe.name}/history?{query_string}"
    response = client.get(
        url,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert "items" in data
    assert "meta" in data
    assert "count" in data["meta"]
    assert "skip" in data["meta"]
    assert "page_size" in data["meta"]
    assert data["meta"]["page_size"] == expected_count


@pytest.mark.parametrize(
    "permission,expected_status_code",
    [
        pytest.param(RoleEnum.ADMIN, HTTPStatus.OK, id="admin"),
        pytest.param(RoleEnum.PROCESSOR, HTTPStatus.FORBIDDEN, id="processor"),
    ],
)
def test_get_recipe_history_entry(
    client: TestClient,
    dbsession: OrmSession,
    create_account: Callable[..., Account],
    create_recipe: Callable[..., Recipe],
    permission: RoleEnum,
    expected_status_code: HTTPStatus,
):
    account = create_account(permission=permission)
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )

    recipe = create_recipe(name="test_recipe")
    dbsession.add(recipe)
    dbsession.flush()

    response = client.get(
        f"/v2/recipes/{recipe.name}/history/{recipe.history_entries[0].id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == expected_status_code


def test_get_recipe_backups(
    client: TestClient,
    create_account: Callable[..., Account],
    create_recipe: Callable[..., Recipe],
    create_recipe_config: Callable[..., RecipeConfigSchema],
    mwoffliner_definition: OfflinerDefinitionSchema,  # noqa: ARG001 needed for side effect
):
    account = create_account(permission=RoleEnum.ADMIN)
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )

    create_recipe(recipe_config=create_recipe_config())

    response = client.get(
        "/v2/recipes/backup",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(
    "permission,expected_status_code",
    [
        pytest.param(RoleEnum.ADMIN, HTTPStatus.NO_CONTENT, id="admin"),
        pytest.param(RoleEnum.PROCESSOR, HTTPStatus.FORBIDDEN, id="processor"),
    ],
)
def test_restore_recipes(
    client: TestClient,
    create_account: Callable[..., Account],
    create_recipe: Callable[..., Recipe],
    permission: RoleEnum,
    expected_status_code: HTTPStatus,
):
    account = create_account(permission=permission)
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )

    recipe = create_recipe(name="test_recipe", archived=True)

    response = client.post(
        "/v2/recipes/restore",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"recipe_names": [recipe.name]},
    )
    assert response.status_code == expected_status_code


@pytest.mark.parametrize(
    "permission,expected_status_code",
    [
        pytest.param(RoleEnum.ADMIN, HTTPStatus.OK, id="admin"),
        pytest.param(RoleEnum.PROCESSOR, HTTPStatus.FORBIDDEN, id="processor"),
    ],
)
def test_archive_recipe(
    client: TestClient,
    create_account: Callable[..., Account],
    create_recipe: Callable[..., Recipe],
    permission: RoleEnum,
    expected_status_code: HTTPStatus,
):
    account = create_account(permission=permission)
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )

    recipe = create_recipe(name="test_recipe")

    response = client.patch(
        f"/v2/recipes/{recipe.name}/archive",
        headers={"Authorization": f"Bearer {access_token}"},
        json={},
    )
    assert response.status_code == expected_status_code


@pytest.mark.parametrize(
    "permission,expected_status_code",
    [
        pytest.param(RoleEnum.ADMIN, HTTPStatus.OK, id="admin"),
        pytest.param(RoleEnum.PROCESSOR, HTTPStatus.FORBIDDEN, id="processor"),
    ],
)
def test_restore_recipe(
    client: TestClient,
    create_account: Callable[..., Account],
    create_recipe: Callable[..., Recipe],
    permission: RoleEnum,
    expected_status_code: HTTPStatus,
):
    account = create_account(permission=permission)
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )

    recipe = create_recipe(name="test_recipe", archived=True)

    response = client.patch(
        f"/v2/recipes/{recipe.name}/restore",
        headers={"Authorization": f"Bearer {access_token}"},
        json={},
    )
    assert response.status_code == expected_status_code


@pytest.mark.parametrize(
    "permission,expected_status_code",
    [
        pytest.param(RoleEnum.ADMIN, HTTPStatus.OK, id="admin"),
        pytest.param(RoleEnum.PROCESSOR, HTTPStatus.FORBIDDEN, id="processor"),
    ],
)
def test_revert_recipe_history(
    client: TestClient,
    dbsession: OrmSession,
    create_account: Callable[..., Account],
    create_recipe: Callable[..., Recipe],
    recipe_config: RecipeConfigSchema,
    mwoffliner_definition: OfflinerDefinitionSchema,
    permission: RoleEnum,
    expected_status_code: HTTPStatus,
):
    account = create_account(permission=permission)
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )

    recipe = create_recipe(
        name="test_recipe",
        enabled=True,
        tags=["tag1", "tag2"],
        category="wikipedia",
        periodicity="monthly",
        context="initial context",
        recipe_config=recipe_config,
    )
    initial_history_id = recipe.history_entries[0].id

    update_recipe(
        dbsession,
        author_id=account.id,
        recipe_name="test_recipe",
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

    response = client.patch(
        f"/v2/recipes/{recipe.name}/revert/{initial_history_id}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={},
    )
    assert response.status_code == expected_status_code
