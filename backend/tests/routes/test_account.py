from collections.abc import Callable
from contextlib import nullcontext as does_not_raise
from http import HTTPStatus
from typing import Any
from uuid import UUID

import pytest
from _pytest.raises import RaisesExc
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.api.routes.accounts.models import AccountCreateSchema
from zimfarm_backend.api.token import generate_access_token
from zimfarm_backend.common import getnow
from zimfarm_backend.common.roles import RoleEnum
from zimfarm_backend.db.models import Account, Team, TeamPermission


@pytest.mark.parametrize(
    "username,display_name,password,role,expected",
    [
        pytest.param(
            None,
            None,
            "testpassword",
            RoleEnum.ADMIN,
            pytest.raises(ValidationError),
            id="no-username-and-displayname",
        ),
        pytest.param(
            "testuser",
            None,
            "testpassword",
            RoleEnum.WORKER,
            pytest.raises(ValidationError),
            id="worker-role",
        ),
        pytest.param(
            None,
            "Test User",
            "testpassword",
            RoleEnum.GLOBAL_EDITOR,
            pytest.raises(ValidationError),
            id="no-username-with-password",
        ),
        pytest.param(
            "testuser",
            "Test User",
            "testpassword",
            RoleEnum.GLOBAL_EDITOR,
            does_not_raise(),
            id="valid-inputs",
        ),
    ],
)
def test_account_creation_schema(
    username: str | None,
    display_name: str | None,
    password: str | None,
    role: RoleEnum,
    expected: RaisesExc[Exception],
):
    with expected:
        AccountCreateSchema(
            username=username,
            display_name=display_name,
            password=password,
            role=role,
        )


def test_display_username_set_from_username_if_no_display_name():
    account = AccountCreateSchema(
        username="testuser",
        role=RoleEnum.ADMIN,
        password="testpassword",
    )

    assert account.display_name is not None


def test_list_accounts_no_auth(client: TestClient):
    response = client.get("/v2/accounts")
    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.num_accounts(5)
def test_list_accounts_no_param(client: TestClient, accounts: list[Account]):
    account = accounts[0]
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )
    response = client.get(
        "/v2/accounts", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == HTTPStatus.OK

    response_json = response.json()
    assert "items" in response_json
    assert "meta" in response_json
    assert response_json["meta"]["count"] == 5
    assert len(response_json["items"]) == len(accounts)
    for item in response_json["items"]:
        item_keys = item.keys()
        assert "username" in item_keys
        assert "id" in item_keys
        assert "display_name" in item_keys
        assert "role" in item_keys
        assert "scope" in item_keys
        assert "idp_sub" in item_keys


@pytest.mark.parametrize("skip, limit, expected", [(0, 1, 1), (1, 10, 4), (0, 100, 5)])
@pytest.mark.num_accounts(5)
def test_list_accounts_with_param(
    client: TestClient,
    accounts: list[Account],
    skip: int,
    limit: int,
    expected: int,
):
    account = accounts[0]
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )
    url = f"/v2/accounts?skip={skip}&limit={limit}"
    response = client.get(url, headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == HTTPStatus.OK

    response_json = response.json()
    assert "items" in response_json
    assert "meta" in response_json
    assert response_json["meta"]["count"] == 5
    assert len(response_json["items"]) == expected


@pytest.mark.num_accounts(10)
def test_skip_deleted_accounts(
    dbsession: OrmSession,
    client: TestClient,
    accounts: list[Account],
):
    account = accounts[0]
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )
    for i in range(1, len(accounts)):
        accounts[i].deleted = True
        dbsession.add(accounts[i])
        dbsession.flush()

    url = f"/v2/accounts?skip={0}&limit={100}"
    response = client.get(url, headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == HTTPStatus.OK

    response_json = response.json()
    assert "items" in response_json
    assert "meta" in response_json
    assert response_json["meta"]["count"] == 1  # skip deleted accounts
    assert len(response_json["items"]) == 1


def test_get_account_by_username(client: TestClient, account: Account):
    url = f"/v2/accounts/{account.username}"
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )
    response = client.get(url, headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == HTTPStatus.OK

    response_json = response.json()
    assert response_json["username"] == account.username


def test_get_account_by_username_not_found(
    client: TestClient,
    account: Account,
):
    url = f"/v2/accounts/{account.username}1"
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )
    response = client.get(url, headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_create_account(client: TestClient, account: Account):
    url = "/v2/accounts/"
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )
    response = client.post(
        url,
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "username": "test",
            "password": "testpassword",
            "role": "admin",
        },
    )
    assert response.status_code == HTTPStatus.OK


def test_create_account_duplicate(client: TestClient, account: Account):
    url = "/v2/accounts/"
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )
    response = client.post(
        url,
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "username": account.username,
            "password": "testpassword",
            "role": "admin",
        },
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_update_account_role(client: TestClient, account: Account):
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )
    url = f"/v2/accounts/{account.username}"
    response = client.patch(
        url,
        headers={"Authorization": f"Bearer {access_token}"},
        json={"role": "global-editor"},
    )
    assert response.status_code == HTTPStatus.NO_CONTENT

    # Verify the role is updated and scope is None
    response = client.get(url, headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["username"] == account.username
    assert data["role"] == "global-editor"


def test_update_account_scope(client: TestClient, account: Account):
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )
    url = f"/v2/accounts/{account.username}"
    response = client.patch(
        url,
        headers={"Authorization": f"Bearer {access_token}"},
        json={"scope": {"recipes": {"read": True}}},
    )
    assert response.status_code == HTTPStatus.NO_CONTENT

    # Verify the role is updated and scope is None
    response = client.get(url, headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["username"] == account.username


def test_update_account_role_and_scope(client: TestClient, account: Account):
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )
    url = f"/v2/accounts/{account.username}"
    response = client.patch(
        url,
        headers={"Authorization": f"Bearer {access_token}"},
        json={"scope": {"recipes": {"read": True}}, "role": "global-editor"},
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.num_accounts(2, permission="global-editor")
def test_update_account_password_wrong_permission(
    client: TestClient, accounts: list[Account]
):
    """Test updating an account's password without permission"""
    account = accounts[0]
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )
    response = client.patch(
        f"/v2/accounts/{accounts[1].username}/password",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"current": "test", "new": "test2"},
    )
    assert response.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.parametrize(
    "current,new,expected",
    [
        pytest.param(
            "invalid", "test2", HTTPStatus.BAD_REQUEST, id="invalid-current-password"
        ),
        pytest.param(None, "test2", HTTPStatus.BAD_REQUEST, id="no-current-password"),
        pytest.param(
            "testpassword", "test2", HTTPStatus.NO_CONTENT, id="change-password"
        ),
        pytest.param(
            "testpassword", None, HTTPStatus.NO_CONTENT, id="set-password-to-None"
        ),
    ],
)
def test_update_account_own_password(
    client: TestClient,
    create_account: Callable[..., Account],
    current: str,
    new: str,
    expected: HTTPStatus,
):
    """Test updating an account's own password"""
    account = create_account(permission="global-editor")
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )
    response = client.patch(
        f"/v2/accounts/{account.username}/password",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"current": current, "new": new},
    )
    assert response.status_code == expected


def _account_team_names(session: OrmSession, account_id: UUID) -> set[str]:
    return set(
        session.scalars(
            select(Team.name)
            .join(TeamPermission, TeamPermission.team_id == Team.id)
            .where(TeamPermission.account_id == account_id)
        )
    )


@pytest.mark.parametrize(
    "role,teams,expected_status_code",
    [
        pytest.param(
            RoleEnum.TEAM_EDITOR, ["wikimedia"], HTTPStatus.OK, id="team-editor"
        ),
        pytest.param(
            RoleEnum.TEAM_VIEWER,
            ["wikimedia", "openzim"],
            HTTPStatus.OK,
            id="team-viewer",
        ),
        pytest.param(RoleEnum.ADMIN, None, HTTPStatus.OK, id="admin"),
        pytest.param(
            RoleEnum.TEAM_EDITOR,
            None,
            HTTPStatus.UNPROCESSABLE_ENTITY,
            id="team-editor-without-teams",
        ),
        pytest.param(
            RoleEnum.ADMIN,
            ["wikimedia"],
            HTTPStatus.UNPROCESSABLE_ENTITY,
            id="admin-with-teams",
        ),
    ],
)
def test_create_account_with_teams(
    client: TestClient,
    account: Account,
    create_team: Callable[..., Team],
    dbsession: OrmSession,
    role: RoleEnum,
    teams: list[str] | None,
    expected_status_code: HTTPStatus,
):
    """Test that creating an account assigns team permissions for team roles"""
    create_team(name="wikimedia")
    create_team(name="openzim")
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )
    payload: dict[str, Any] = {
        "username": "newuser",
        "password": "testpassword",
        "role": role.value,
    }
    if teams is not None:
        payload["teams"] = teams

    response = client.post(
        "/v2/accounts/",
        headers={"Authorization": f"Bearer {access_token}"},
        json=payload,
    )
    assert response.status_code == expected_status_code
    if expected_status_code == HTTPStatus.OK:
        created_id = UUID(response.json()["id"])
        assert _account_team_names(dbsession, created_id) == set(teams or [])


@pytest.mark.parametrize(
    "teams,expected_team_names",
    [
        pytest.param(
            ["wikimedia", "openzim"],
            {"wikimedia", "openzim"},
            id="two-teams",
        ),
        pytest.param(["wikimedia"], {"wikimedia"}, id="one-team"),
        pytest.param([], set[str](), id="no-teams"),
    ],
)
def test_update_account_teams(
    client: TestClient,
    account: Account,
    create_account: Callable[..., Account],
    create_team: Callable[..., Team],
    dbsession: OrmSession,
    teams: list[str],
    expected_team_names: set[str],
):
    """Test that updating an account role/teams replaces its team permissions"""
    create_team(name="wikimedia")
    create_team(name="openzim")
    target = create_account(permission=RoleEnum.PUBLIC_VIEWER)
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )

    response = client.patch(
        f"/v2/accounts/{target.username}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "display_name": target.display_name,
            "role": RoleEnum.TEAM_EDITOR.value,
            "teams": teams,
        },
    )
    assert response.status_code == HTTPStatus.NO_CONTENT
    assert _account_team_names(dbsession, target.id) == expected_team_names

    # switching to a non-team role clears the team permissions
    response = client.patch(
        f"/v2/accounts/{target.username}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "display_name": target.display_name,
            "role": RoleEnum.GLOBAL_VIEWER.value,
        },
    )
    assert response.status_code == HTTPStatus.NO_CONTENT
    assert _account_team_names(dbsession, target.id) == set[str]()
