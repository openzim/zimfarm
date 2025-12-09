from collections.abc import Callable
from http import HTTPStatus
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.api.token import generate_access_token
from zimfarm_backend.common import getnow
from zimfarm_backend.common.enums import ScheduleCategory, SchedulePeriodicity
from zimfarm_backend.common.roles import RoleEnum
from zimfarm_backend.common.schemas.models import ScheduleConfigSchema
from zimfarm_backend.common.schemas.orms import (
    LanguageSchema,
    OfflinerDefinitionSchema,
    OfflinerSchema,
)
from zimfarm_backend.db.models import RequestedTask, Schedule, Task, User
from zimfarm_backend.db.offliner_definition import create_offliner_definition_schema
from zimfarm_backend.db.schedule import get_schedule, update_schedule


@pytest.mark.parametrize(
    "query_string,expected_count",
    [
        pytest.param("", 10, id="all"),
        pytest.param("&name=wiki&lang=eng", 10, id="wiki_eng"),
        pytest.param("&name=wiki&lang=fra", 0, id="wiki_fra"),
        pytest.param("&name=schedule&category=wikipedia", 0, id="schedule_wikipedia"),
        pytest.param("&name=schedule&lang=eng&tag=important", 0, id="eng_important"),
        pytest.param("&name=nonexistent", 0, id="nonexistent"),
        pytest.param(
            "&name=schedule&lang=eng&category=other&tag=test",
            0,
            id="schedule_eng_other_test",
        ),
        pytest.param(
            "&name=wiki&lang=eng&category=wikipedia&tag=important",
            10,
            id="wiki_eng_important",
        ),
    ],
)
def test_get_schedules(
    client: TestClient,
    dbsession: OrmSession,
    create_user: Callable[..., User],
    create_schedule: Callable[..., Schedule],
    create_requested_task: Callable[..., RequestedTask],
    create_task: Callable[..., Task],
    query_string: str,
    expected_count: int,
):
    user = create_user(permission=RoleEnum.PROCESSOR)
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
    )

    for i in range(10):
        schedule = create_schedule(
            name=f"wiki_eng_{i}",
            category=ScheduleCategory.wikipedia,
            language=LanguageSchema(code="eng", name="English"),
            tags=["important"],
        )
        requested_task = create_requested_task(schedule_name=schedule.name)
        task = create_task(requested_task=requested_task)
        schedule.most_recent_task = task
        schedule.similarity_data = ["hello", "world"]
        dbsession.add(schedule)
        dbsession.flush()

    url = "/v2/schedules?skip=0&limit=5"
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
        pytest.param(RoleEnum.PROCESSOR, HTTPStatus.UNAUTHORIZED, id="processor"),
    ],
)
def test_get_archived_schedules(
    client: TestClient,
    create_user: Callable[..., User],
    create_schedule: Callable[..., Schedule],
    permission: RoleEnum,
    expected_status_code: HTTPStatus,
):
    user = create_user(permission=permission)
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
        username=user.username,
        email=user.email,
        scope=user.scope,
    )
    create_schedule(name="test_schedule", archived=True)

    response = client.get(
        "/v2/schedules?skip=0&limit=1&archived=true",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == expected_status_code


def test_get_similar_schedules(
    client: TestClient,
    dbsession: OrmSession,
    create_user: Callable[..., User],
    create_schedule: Callable[..., Schedule],
    create_requested_task: Callable[..., RequestedTask],
    create_task: Callable[..., Task],
):
    user = create_user(permission=RoleEnum.PROCESSOR)
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
    )

    for i in range(10):
        schedule = create_schedule(
            name=f"wiki_eng_{i}",
            category=ScheduleCategory.wikipedia,
            language=LanguageSchema(code="eng", name="English"),
            tags=["important"],
        )
        requested_task = create_requested_task(schedule_name=schedule.name)
        task = create_task(requested_task=requested_task)
        schedule.most_recent_task = task
        schedule.similarity_data = ["hello", "world"]
        dbsession.add(schedule)
        dbsession.flush()

    url = "/v2/schedules/wiki_eng_0/similar?skip=0&limit=5"
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
    assert data["meta"]["count"] == 9  # schedule itself is not included
    assert len(data["items"]) <= 5


@pytest.mark.parametrize(
    "payload,expected_status_code",
    [
        pytest.param(
            {
                "name": "test_schedule",
                "category": ScheduleCategory.wikipedia.value,
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
                "periodicity": SchedulePeriodicity.manually.value,
                "version": "initial",
            },
            HTTPStatus.UNPROCESSABLE_ENTITY,
            id="invalid-config-missing-offliner-id",
        ),
        pytest.param(
            {
                "name": "test_schedule",
                "category": ScheduleCategory.wikipedia.value,
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
                "periodicity": SchedulePeriodicity.manually.value,
                "version": "initial",
            },
            HTTPStatus.UNPROCESSABLE_ENTITY,
            id="invalid-config-extra-keys",
        ),
        pytest.param(
            {
                "name": "test_schedule",
                "category": ScheduleCategory.wikipedia.value,
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
                "periodicity": SchedulePeriodicity.manually.value,
                "version": "notfound",
            },
            HTTPStatus.NOT_FOUND,
            id="valid-config-offliner-version-does-not-exist",
        ),
        pytest.param(
            {
                "name": "test_schedule",
                "category": ScheduleCategory.wikipedia.value,
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
                "periodicity": SchedulePeriodicity.manually.value,
                "context": "test",
                "version": "initial",
            },
            HTTPStatus.OK,
            id="valid-config",
        ),
    ],
)
def test_create_schedule(
    client: TestClient,
    create_user: Callable[..., User],
    mwoffliner_definition: OfflinerDefinitionSchema,  # noqa: ARG001
    payload: dict[str, Any],
    expected_status_code: HTTPStatus,
):
    """Test that create_schedule raises Unprocessable Entity with invalid config"""
    user = create_user(permission=RoleEnum.ADMIN)
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
    )

    response = client.post(
        "/v2/schedules",
        headers={"Authorization": f"Bearer {access_token}"},
        json=payload,
    )
    assert response.status_code == expected_status_code


@pytest.mark.parametrize(
    "permission,expected_status_code",
    [
        pytest.param(RoleEnum.ADMIN, HTTPStatus.OK, id="admin"),
        pytest.param(RoleEnum.PROCESSOR, HTTPStatus.UNAUTHORIZED, id="processor"),
    ],
)
def test_create_schedule_with_permssions(
    client: TestClient,
    dbsession: OrmSession,
    create_user: Callable[..., User],
    create_schedule_config: Callable[..., ScheduleConfigSchema],
    mwoffliner_definition: OfflinerDefinitionSchema,
    permission: RoleEnum,
    expected_status_code: HTTPStatus,
):
    """Test that create_schedule raises ForbiddenError without permission"""
    user = create_user(permission=permission)
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
    )

    schedule_config = create_schedule_config()

    response = client.post(
        "/v2/schedules",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "name": "test_schedule",
            "category": ScheduleCategory.wikipedia.value,
            "language": "eng",
            "tags": ["important"],
            "config": schedule_config.model_dump(
                mode="json", context={"show_secrets": True}
            ),
            "enabled": True,
            "periodicity": SchedulePeriodicity.manually.value,
            "version": mwoffliner_definition.version,
            "context": "test",
        },
    )
    assert response.status_code == expected_status_code
    if response.status_code == HTTPStatus.OK:
        # assert top-level scalar attributes of the schedule with the payload
        schedule = get_schedule(dbsession, schedule_name="test_schedule")
        assert schedule.language_code == "eng"
        assert schedule.tags == ["important"]
        assert schedule.enabled is True
        assert schedule.context == "test"
        assert schedule.periodicity == SchedulePeriodicity.manually.value
        assert schedule.category == ScheduleCategory.wikipedia.value


@pytest.mark.parametrize(
    "schedule_name,expected_status_code",
    [
        pytest.param("test_schedule", HTTPStatus.OK, id="valid-schedule-name"),
        pytest.param(
            "test-schedule/",
            HTTPStatus.UNPROCESSABLE_ENTITY,
            id="slash-in-schedule-name",
        ),
        pytest.param(
            "none", HTTPStatus.UNPROCESSABLE_ENTITY, id="none-as-schedule-name"
        ),
        pytest.param(
            "testSchedule", HTTPStatus.UNPROCESSABLE_ENTITY, id="uppercase-char"
        ),
    ],
)
def test_schedule_name(
    client: TestClient,
    create_user: Callable[..., User],
    create_schedule_config: Callable[..., ScheduleConfigSchema],
    mwoffliner_definition: OfflinerDefinitionSchema,
    schedule_name: str,
    expected_status_code: int,
):
    """Test that create_schedule raises Unprocessable entity with invalid name"""
    user = create_user(permission=RoleEnum.ADMIN)
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
    )

    schedule_config = create_schedule_config()

    response = client.post(
        "/v2/schedules",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "name": schedule_name,
            "category": ScheduleCategory.wikipedia.value,
            "language": "eng",
            "tags": ["important"],
            "config": schedule_config.model_dump(
                mode="json", context={"show_secrets": True}
            ),
            "enabled": True,
            "periodicity": SchedulePeriodicity.manually.value,
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
def test_get_schedule(
    client: TestClient,
    dbsession: OrmSession,
    create_user: Callable[..., User],
    create_schedule: Callable[..., Schedule],
    permission: RoleEnum,
    *,
    hide_secrets: bool,
):
    user = create_user(permission=permission)
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
    )

    schedule = create_schedule(name="test_schedule")
    dbsession.add(schedule)
    dbsession.flush()

    _hide_secrets = "true" if hide_secrets else "false"
    response = client.get(
        f"/v2/schedules/{schedule.name}?hide_secrets={_hide_secrets}",
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


def test_get_obsolete_schedule(
    client: TestClient,
    dbsession: OrmSession,
    create_user: Callable[..., User],
    create_schedule: Callable[..., Schedule],
    create_schedule_config: Callable[..., ScheduleConfigSchema],
    mwoffliner: OfflinerSchema,  # noqa: ARG001 needed for side effect
    mwoffliner_definition: OfflinerDefinitionSchema,  # noqa: ARG001 needed for side effect
):
    user = create_user(permission=RoleEnum.ADMIN)
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
    )

    schedule_config = create_schedule_config()
    raw_schedule_config = schedule_config.model_dump(
        mode="json", context={"show_secrets": True}
    )
    raw_schedule_config["offliner"]["mwUrl"] = None  # Unset mandatory field
    raw_schedule_config["offliner"]["oldFlag"] = "anyValue"  # Set unknown field
    schedule = create_schedule(
        name="test_schedule", raw_schedule_config=raw_schedule_config
    )
    dbsession.add(schedule)
    dbsession.flush()

    response = client.get(
        f"/v2/schedules/{schedule.name}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == HTTPStatus.OK
    schedule_data = response.json()
    assert "config" in schedule_data
    assert "offliner" in schedule_data["config"]
    assert "mwUrl" in schedule_data["config"]["offliner"]
    assert schedule_data["config"]["offliner"]["mwUrl"] is None
    assert "oldFlag" in schedule_data["config"]["offliner"]
    assert schedule_data["config"]["offliner"]["oldFlag"] == "anyValue"


def test_patch_obsolete_schedule(
    client: TestClient,
    dbsession: OrmSession,
    create_user: Callable[..., User],
    create_schedule: Callable[..., Schedule],
    create_schedule_config: Callable[..., ScheduleConfigSchema],
    mwoffliner: OfflinerSchema,  # noqa: ARG001 needed for side effect
    mwoffliner_definition: OfflinerDefinitionSchema,  # noqa: ARG001 needed for side effect
):
    user = create_user(permission=RoleEnum.ADMIN)
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
    )

    schedule_config = create_schedule_config()
    raw_schedule_config = schedule_config.model_dump(
        mode="json", context={"show_secrets": True}
    )
    raw_schedule_config["offliner"]["mwUrl"] = None  # Unset mandatory field
    raw_schedule_config["offliner"]["oldFlag"] = "anyValue"  # Set unknown field
    schedule = create_schedule(
        name="test_schedule", raw_schedule_config=raw_schedule_config
    )
    dbsession.add(schedule)
    dbsession.flush()

    response = client.patch(
        f"/v2/schedules/{schedule.name}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "flags": {"mwUrl": "http://fr.wikipedia.org", "adminEmail": "bob@acme.com"},
        },
    )

    assert response.status_code == HTTPStatus.OK
    schedule_data = response.json()
    assert "config" in schedule_data
    assert "offliner" in schedule_data["config"]
    assert "mwUrl" in schedule_data["config"]["offliner"]
    assert schedule_data["config"]["offliner"]["mwUrl"] == "http://fr.wikipedia.org/"
    assert "oldFlag" not in schedule_data["config"]["offliner"]


def test_update_schedule_unauthorized(
    client: TestClient,
    create_user: Callable[..., User],
):
    """Test that update_schedule raises ForbiddenError without permission"""
    user = create_user(permission=RoleEnum.PROCESSOR)
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
    )

    response = client.patch(
        "/v2/schedules/nonexistent",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "name": "test_schedule",
            "category": ScheduleCategory.wikipedia.value,
        },
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


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
def test_update_schedule(
    client: TestClient,
    dbsession: OrmSession,
    create_user: Callable[..., User],
    create_schedule: Callable[..., Schedule],
    mwoffliner: OfflinerSchema,  # noqa: ARG001 needed for side effect
    mwoffliner_definition: OfflinerDefinitionSchema,  # noqa: ARG001 needed for side effect
    tedoffliner_definition: OfflinerDefinitionSchema,  # noqa: ARG001 needed for side effect
    ted_offliner: OfflinerSchema,  # noqa: ARG001 needed for side effect
    payload: dict[str, Any],
    expected_status_code: HTTPStatus,
):
    user = create_user(permission=RoleEnum.ADMIN)
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
    )

    schedule = create_schedule(name="test_schedule")
    dbsession.add(schedule)
    dbsession.flush()

    response = client.patch(
        f"/v2/schedules/{schedule.name}",
        headers={"Authorization": f"Bearer {access_token}"},
        json=payload,
    )
    assert response.status_code == expected_status_code


@pytest.mark.parametrize(
    "permission,expected_status_code",
    [
        pytest.param(RoleEnum.ADMIN, HTTPStatus.NO_CONTENT, id="admin"),
        pytest.param(RoleEnum.PROCESSOR, HTTPStatus.UNAUTHORIZED, id="processor"),
    ],
)
def test_delete_schedule(
    client: TestClient,
    dbsession: OrmSession,
    create_user: Callable[..., User],
    create_schedule: Callable[..., Schedule],
    permission: RoleEnum,
    expected_status_code: HTTPStatus,
):
    user = create_user(permission=permission)
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
    )

    schedule = create_schedule(name="test_schedule")
    dbsession.add(schedule)
    dbsession.flush()

    response = client.delete(
        f"/v2/schedules/{schedule.name}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == expected_status_code


def test_get_schedule_image_names(
    client: TestClient,
    dbsession: OrmSession,
    create_schedule: Callable[..., Schedule],
):
    schedule = create_schedule(name="test_schedule")
    dbsession.add(schedule)
    dbsession.flush()

    response = client.get(
        f"/v2/schedules/{schedule.name}/image-names?hub_name=openzim/mwoffliner",
    )
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert "items" in data
    for item in data["items"]:
        assert isinstance(item, str)


@pytest.mark.parametrize(
    "new_language_code,expected_validity_status",
    [
        pytest.param("invalid", False, id="invalid-language-code"),
        pytest.param("eng", True, id="valid-language-code"),
    ],
)
def test_clone_schedule(
    client: TestClient,
    dbsession: OrmSession,
    create_user: Callable[..., User],
    create_schedule: Callable[..., Schedule],
    new_language_code: str,
    *,
    expected_validity_status: bool,
):
    user = create_user(permission=RoleEnum.ADMIN)
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
    )

    schedule = create_schedule(name="test_schedule")
    schedule.language_code = new_language_code
    dbsession.add(schedule)
    dbsession.flush()

    response = client.post(
        f"/v2/schedules/{schedule.name}/clone",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"name": "test_schedule_clone"},
    )
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert "id" in data
    assert data["id"] is not None
    assert str(data["id"]) != str(schedule.id)

    new_schedule = get_schedule(dbsession, schedule_name="test_schedule_clone")
    assert new_schedule.is_valid == expected_validity_status


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
            HTTPStatus.UNAUTHORIZED,
            id="valid-language-code-processor",
        ),
    ],
)
def test_validate_schedule(
    client: TestClient,
    dbsession: OrmSession,
    create_user: Callable[..., User],
    create_schedule: Callable[..., Schedule],
    permission: RoleEnum,
    new_language_code: str,
    *,
    expected_status_code: HTTPStatus,
):
    user = create_user(permission=permission)
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
    )
    schedule = create_schedule(name="test_schedule")
    # set the new language code in the db
    schedule.language_code = new_language_code
    dbsession.add(schedule)
    dbsession.flush()

    response = client.get(
        f"/v2/schedules/{schedule.name}/validate",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == expected_status_code


def test_create_duplicate_schedule(
    client: TestClient,
    dbsession: OrmSession,
    create_user: Callable[..., User],
    create_schedule: Callable[..., Schedule],
    create_schedule_config: Callable[..., ScheduleConfigSchema],
):
    schedule_config = create_schedule_config()
    schedule = create_schedule(name="test_schedule", schedule_config=schedule_config)
    dbsession.add(schedule)
    dbsession.flush()

    user = create_user(permission=RoleEnum.ADMIN)
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
    )

    response = client.post(
        "/v2/schedules",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "name": "test_schedule",
            "category": ScheduleCategory.wikipedia.value,
            "language": "eng",
            "tags": ["important"],
            "config": schedule_config.model_dump(
                mode="json", context={"show_secrets": True}
            ),
            "enabled": True,
            "periodicity": SchedulePeriodicity.manually.value,
            "version": "initial",
        },
    )
    assert response.status_code == HTTPStatus.CONFLICT


def test_clone_existing_schedule_with_name_unchanged(
    client: TestClient,
    dbsession: OrmSession,
    create_user: Callable[..., User],
    create_schedule: Callable[..., Schedule],
    create_schedule_config: Callable[..., ScheduleConfigSchema],
):
    user = create_user(permission=RoleEnum.ADMIN)
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
    )

    schedule_config = create_schedule_config()
    schedule = create_schedule(name="test_schedule", schedule_config=schedule_config)
    dbsession.add(schedule)
    dbsession.flush()

    response = client.post(
        f"/v2/schedules/{schedule.name}/clone",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"name": "test_schedule"},
    )
    assert response.status_code == HTTPStatus.CONFLICT


def test_update_existing_schedule_with_existing_name(
    client: TestClient,
    dbsession: OrmSession,
    create_user: Callable[..., User],
    create_schedule: Callable[..., Schedule],
    create_schedule_config: Callable[..., ScheduleConfigSchema],
):
    """Test that updating a schedule name with another existing schedule name fails"""
    user = create_user(permission=RoleEnum.ADMIN)
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
    )

    schedule_config = create_schedule_config()
    schedules = [
        create_schedule(name=f"test_schedule_{i}", schedule_config=schedule_config)
        for i in range(3)
    ]
    dbsession.add_all(schedules)
    dbsession.flush()

    # attempt to update schedule_1 with the name of schedule_2
    response = client.patch(
        "/v2/schedules/test_schedule_1",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "name": "test_schedule_2",
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
def test_update_schedule_config_top_level_attributes(
    client: TestClient,
    dbsession: OrmSession,
    create_user: Callable[..., User],
    create_schedule: Callable[..., Schedule],
    payload: dict[str, Any],
    check_attrs: set[str],
    expected_status_code: HTTPStatus,
):
    user = create_user(permission=RoleEnum.ADMIN)
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
    )

    schedule = create_schedule(name="test_schedule")
    dbsession.add(schedule)
    dbsession.flush()

    response = client.patch(
        f"/v2/schedules/{schedule.name}",
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
        pytest.param(RoleEnum.PROCESSOR, HTTPStatus.UNAUTHORIZED, id="processor"),
    ],
)
def test_get_schedule_history(
    client: TestClient,
    dbsession: OrmSession,
    create_user: Callable[..., User],
    create_schedule: Callable[..., Schedule],
    permission: RoleEnum,
    expected_status_code: HTTPStatus,
):
    user = create_user(permission=permission)
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
    )

    schedule = create_schedule(name="test_schedule")
    dbsession.add(schedule)
    dbsession.flush()

    response = client.get(
        f"/v2/schedules/{schedule.name}/history?limit=10&skip=0",
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
def test_get_schedule_history_pagination(
    client: TestClient,
    dbsession: OrmSession,
    create_user: Callable[..., User],
    create_schedule: Callable[..., Schedule],
    query_string: str,
    expected_count: int,
):
    user = create_user(username="test", permission=RoleEnum.ADMIN)
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
    )
    schedule = create_schedule(
        name="test_schedule",
        category=ScheduleCategory.wikipedia,
        language=LanguageSchema(code="eng", name="English"),
        tags=["important"],
    )

    #  When we created a schedule, we created 1 history entry
    for i in range(9):
        update_schedule(
            session=dbsession,
            author=user.username,
            schedule_name=schedule.name,
            comment=f"test_comment_{i}",
            tags=[*schedule.tags, f"test_tag_{i}"],
            offliner_definition=create_offliner_definition_schema(
                schedule.offliner_definition
            ),
        )

    url = f"/v2/schedules/{schedule.name}/history?{query_string}"
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
        pytest.param(RoleEnum.PROCESSOR, HTTPStatus.UNAUTHORIZED, id="processor"),
    ],
)
def test_get_schedule_history_entry(
    client: TestClient,
    dbsession: OrmSession,
    create_user: Callable[..., User],
    create_schedule: Callable[..., Schedule],
    permission: RoleEnum,
    expected_status_code: HTTPStatus,
):
    user = create_user(permission=permission)
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
    )

    schedule = create_schedule(name="test_schedule")
    dbsession.add(schedule)
    dbsession.flush()

    response = client.get(
        f"/v2/schedules/{schedule.name}/history/{schedule.history_entries[0].id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == expected_status_code


def test_get_schedule_backups(
    client: TestClient,
    create_user: Callable[..., User],
    create_schedule: Callable[..., Schedule],
    create_schedule_config: Callable[..., ScheduleConfigSchema],
    mwoffliner_definition: OfflinerDefinitionSchema,  # noqa: ARG001 needed for side effect
):
    user = create_user(permission=RoleEnum.ADMIN)
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
    )

    create_schedule(schedule_config=create_schedule_config())

    response = client.get(
        "/v2/schedules/backup",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(
    "permission,expected_status_code",
    [
        pytest.param(RoleEnum.ADMIN, HTTPStatus.NO_CONTENT, id="admin"),
        pytest.param(RoleEnum.PROCESSOR, HTTPStatus.UNAUTHORIZED, id="processor"),
    ],
)
def test_restore_schedules(
    client: TestClient,
    create_user: Callable[..., User],
    create_schedule: Callable[..., Schedule],
    permission: RoleEnum,
    expected_status_code: HTTPStatus,
):
    user = create_user(permission=permission)
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
    )

    schedule = create_schedule(name="test_schedule", archived=True)

    response = client.post(
        "/v2/schedules/restore",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"schedule_names": [schedule.name]},
    )
    assert response.status_code == expected_status_code


@pytest.mark.parametrize(
    "permission,expected_status_code",
    [
        pytest.param(RoleEnum.ADMIN, HTTPStatus.OK, id="admin"),
        pytest.param(RoleEnum.PROCESSOR, HTTPStatus.UNAUTHORIZED, id="processor"),
    ],
)
def test_archive_schedule(
    client: TestClient,
    create_user: Callable[..., User],
    create_schedule: Callable[..., Schedule],
    permission: RoleEnum,
    expected_status_code: HTTPStatus,
):
    user = create_user(permission=permission)
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
    )

    schedule = create_schedule(name="test_schedule")

    response = client.patch(
        f"/v2/schedules/{schedule.name}/archive",
        headers={"Authorization": f"Bearer {access_token}"},
        json={},
    )
    assert response.status_code == expected_status_code


@pytest.mark.parametrize(
    "permission,expected_status_code",
    [
        pytest.param(RoleEnum.ADMIN, HTTPStatus.OK, id="admin"),
        pytest.param(RoleEnum.PROCESSOR, HTTPStatus.UNAUTHORIZED, id="processor"),
    ],
)
def test_restore_schedule(
    client: TestClient,
    create_user: Callable[..., User],
    create_schedule: Callable[..., Schedule],
    permission: RoleEnum,
    expected_status_code: HTTPStatus,
):
    user = create_user(permission=permission)
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
    )

    schedule = create_schedule(name="test_schedule", archived=True)

    response = client.patch(
        f"/v2/schedules/{schedule.name}/restore",
        headers={"Authorization": f"Bearer {access_token}"},
        json={},
    )
    assert response.status_code == expected_status_code
