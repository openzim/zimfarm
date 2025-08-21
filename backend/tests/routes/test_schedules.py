from collections.abc import Callable
from http import HTTPStatus
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.common import getnow
from zimfarm_backend.common.enums import ScheduleCategory, SchedulePeriodicity
from zimfarm_backend.common.roles import RoleEnum
from zimfarm_backend.common.schemas.models import ScheduleConfigSchema
from zimfarm_backend.common.schemas.orms import LanguageSchema
from zimfarm_backend.db.models import RequestedTask, Schedule, Task, User
from zimfarm_backend.utils.token import generate_access_token


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
    """Test that get_schedules raises ForbiddenError without permission"""
    user = create_user(permission=RoleEnum.PROCESSOR)
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
        username=user.username,
        email=user.email,
        scope=user.scope,
    )

    for i in range(10):
        schedule = create_schedule(
            name=f"wiki_eng_{i}",
            category=ScheduleCategory.wikipedia,
            language=LanguageSchema(
                code="eng", name_en="English", name_native="English"
            ),
            tags=["important"],
        )
        requested_task = create_requested_task(schedule_name=schedule.name)
        task = create_task(requested_task=requested_task)
        schedule.most_recent_task = task
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
def test_create_schedule(
    client: TestClient,
    create_user: Callable[..., User],
    create_schedule_config: Callable[..., ScheduleConfigSchema],
    permission: RoleEnum,
    expected_status_code: HTTPStatus,
):
    """Test that create_schedule raises ForbiddenError without permission"""
    user = create_user(permission=permission)
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
        username=user.username,
        email=user.email,
        scope=user.scope,
    )

    schedule_config = create_schedule_config()

    response = client.post(
        "/v2/schedules",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "name": "test_schedule",
            "category": ScheduleCategory.wikipedia.value,
            "language": {
                "code": "eng",
                "name_en": "English",
                "name_native": "English",
            },
            "tags": ["important"],
            "config": schedule_config.model_dump(
                mode="json", context={"show_secrets": True}, by_alias=True
            ),
            "enabled": True,
            "periodicity": SchedulePeriodicity.manually.value,
        },
    )
    assert response.status_code == expected_status_code


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
            "  test-schedule  ",
            HTTPStatus.UNPROCESSABLE_ENTITY,
            id="spaces-in-schedule-name",
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
    schedule_name: str,
    expected_status_code: int,
):
    """Test that create_schedule raises Unprocessable entity with invalid name"""
    user = create_user(permission=RoleEnum.ADMIN)
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
        username=user.username,
        email=user.email,
        scope=user.scope,
    )

    schedule_config = create_schedule_config()

    response = client.post(
        "/v2/schedules",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "name": schedule_name,
            "category": ScheduleCategory.wikipedia.value,
            "language": {
                "code": "eng",
                "name_en": "English",
                "name_native": "English",
            },
            "tags": ["important"],
            "config": schedule_config.model_dump(
                mode="json", context={"show_secrets": True}, by_alias=True
            ),
            "enabled": True,
            "periodicity": SchedulePeriodicity.manually.value,
        },
    )
    assert response.status_code == expected_status_code


@pytest.mark.parametrize(
    "permission,hide_secrets,expected_status_code",
    [
        pytest.param(RoleEnum.ADMIN, False, HTTPStatus.OK, id="admin"),
        pytest.param(RoleEnum.ADMIN, True, HTTPStatus.OK, id="admin_hide_secrets"),
    ],
)
def test_get_schedule(
    client: TestClient,
    dbsession: OrmSession,
    create_user: Callable[..., User],
    create_schedule: Callable[..., Schedule],
    permission: RoleEnum,
    hide_secrets: bool,  # noqa: FBT001
    expected_status_code: HTTPStatus,
):
    """Test that get_schedule raises ForbiddenError without permission"""
    user = create_user(permission=permission)
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
        username=user.username,
        email=user.email,
        scope=user.scope,
    )

    schedule = create_schedule(name="test_schedule")
    dbsession.add(schedule)
    dbsession.flush()

    _hide_secrets = "true" if hide_secrets else "false"
    response = client.get(
        f"/v2/schedules/{schedule.name}?hide_secrets={_hide_secrets}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == expected_status_code
    if expected_status_code == HTTPStatus.OK:
        data = response.json()
        assert "config" in data
        assert "offliner" in data["config"]
        assert "mwPassword" in data["config"]["offliner"]
        if hide_secrets:
            for char in data["config"]["offliner"]["mwPassword"]:
                assert char == "*"
        else:
            assert data["config"]["offliner"]["mwPassword"] == "test-password"


def test_update_schedule_unauthorized(
    client: TestClient,
    create_user: Callable[..., User],
):
    """Test that update_schedule raises ForbiddenError without permission"""
    user = create_user(permission=RoleEnum.PROCESSOR)
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
        username=user.username,
        email=user.email,
        scope=user.scope,
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
        # cannot change only offliner, image must be changed as well
        pytest.param(
            {
                "offliner": "youtube",
                "flags": {},
            },
            HTTPStatus.BAD_REQUEST,
            id="different_offliner_flags_missing",
        ),
        # cannot change only image name, offliner must be changed as well
        pytest.param(
            {
                "image": {"name": "openzim/phet", "tag": "latest"},
                "flags": {},
            },
            HTTPStatus.BAD_REQUEST,
            id="different_image_flags_missing",
        ),
        # image name must be aligned with offliner name
        pytest.param(
            {
                "image": {"name": "openzim/phet", "tag": "latest"},
                "offliner": "gutenberg",
                "flags": {},
            },
            HTTPStatus.BAD_REQUEST,
            id="different_image_name",
        ),
        # wrong flags for offliner
        pytest.param(
            {
                "offliner": "phet",
                "flags": {"mwUrl": "http://fr.wikipedia.org"},
                "image": {"name": "openzim/phet", "tag": "latest"},
            },
            HTTPStatus.UNPROCESSABLE_ENTITY,
            id="wrong_flags",
        ),
        pytest.param(
            {
                "offliner": "gutenberg",
                "flags": {},
                "image": {"name": "openzim/gutenberg", "tag": "latest"},
            },
            HTTPStatus.OK,
            id="good_gutenberg_update",
        ),
        pytest.param(
            {
                "offliner": "phet",
                "flags": {"createMul": True, "mulOnly": True},
                "image": {"name": "openzim/phet", "tag": "latest"},
                "artifacts_globs": ["**/*.json"],
            },
            HTTPStatus.OK,
            id="good_phet_update",
        ),
        # update image name only
        pytest.param(
            {
                "image": {"name": "openzim/mwoffliner", "tag": "1.12.2"},
            },
            HTTPStatus.OK,
            id="good_mw_offliner_image_update",
        ),
    ],
)
def test_update_schedule(
    client: TestClient,
    dbsession: OrmSession,
    create_user: Callable[..., User],
    create_schedule: Callable[..., Schedule],
    payload: dict[str, Any],
    expected_status_code: HTTPStatus,
):
    user = create_user(permission=RoleEnum.ADMIN)
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
        username=user.username,
        email=user.email,
        scope=user.scope,
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
        username=user.username,
        email=user.email,
        scope=user.scope,
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


def test_clone_schedule(
    client: TestClient,
    dbsession: OrmSession,
    create_user: Callable[..., User],
    create_schedule: Callable[..., Schedule],
):
    user = create_user(permission=RoleEnum.ADMIN)
    access_token = generate_access_token(
        issue_time=getnow(),
        user_id=str(user.id),
        username=user.username,
        email=user.email,
        scope=user.scope,
    )

    schedule = create_schedule(name="test_schedule")
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
