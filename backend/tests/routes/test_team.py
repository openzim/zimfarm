from collections.abc import Callable
from http import HTTPStatus
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.api.token import generate_access_token
from zimfarm_backend.common import getnow
from zimfarm_backend.common.roles import RoleEnum
from zimfarm_backend.db import team as db_team
from zimfarm_backend.db.models import Account, Team


def _authorization(account: Account) -> dict[str, str]:
    access_token = generate_access_token(
        issue_time=getnow(),
        account_id=str(account.id),
    )
    return {"Authorization": f"Bearer {access_token}"}


def test_list_teams_no_auth(client: TestClient, team: Team):
    """Anonymous visitors can list public teams"""
    response = client.get("/v2/teams")
    assert response.status_code == HTTPStatus.OK

    response_json = response.json()
    assert "items" in response_json
    assert "meta" in response_json
    assert {item["name"] for item in response_json["items"]} == {team.name}


def test_list_teams_excludes_inaccessible_teams(
    client: TestClient,
    team: Team,
    create_team: Callable[..., Team],
    account: Account,
):
    """Accounts do not see teams they cannot access"""
    private_team = create_team(name="private", is_private=True)

    response = client.get("/v2/teams", headers=_authorization(account))
    assert response.status_code == HTTPStatus.OK

    names = {item["name"] for item in response.json()["items"]}
    assert team.name in names
    assert private_team.name in names

    # anonymous visitors only see public teams
    response = client.get("/v2/teams")
    assert response.status_code == HTTPStatus.OK
    names = {item["name"] for item in response.json()["items"]}
    assert team.name in names
    assert private_team.name not in names


def test_list_teams_filter_by_name(
    client: TestClient,
    create_account: Callable[..., Account],
    create_team: Callable[..., Team],
):
    """Teams can be filtered by name"""
    admin = create_account()
    create_team(name="wikimedia")
    create_team(name="openzim")

    response = client.get(
        "/v2/teams", params={"name": "wiki"}, headers=_authorization(admin)
    )
    assert response.status_code == HTTPStatus.OK
    assert {item["name"] for item in response.json()["items"]} == {"wikimedia"}


@pytest.mark.parametrize(
    "is_private,expected",
    [
        pytest.param(True, {"private"}, id="private-only"),
        pytest.param(False, {"Kiwix"}, id="public-only"),
    ],
)
def test_list_teams_filter_by_is_private(
    client: TestClient,
    create_account: Callable[..., Account],
    create_team: Callable[..., Team],
    *,
    is_private: bool,
    expected: set[str],
):
    """Teams can be filtered by privacy"""
    admin = create_account()
    create_team(name="private", is_private=True)

    response = client.get(
        "/v2/teams",
        params={"is_private": is_private},
        headers=_authorization(admin),
    )
    assert response.status_code == HTTPStatus.OK
    assert {item["name"] for item in response.json()["items"]} == expected


def test_get_team_by_name(client: TestClient, team: Team):
    """A team can be retrieved by its name"""
    response = client.get(f"/v2/teams/{team.name}")
    assert response.status_code == HTTPStatus.OK

    response_json = response.json()
    assert response_json["name"] == team.name
    assert response_json["is_private"] == team.is_private
    assert response_json["id"] == str(team.id)


def test_get_team_by_id(client: TestClient, team: Team):
    """A team can be retrieved by its ID"""
    response = client.get(f"/v2/teams/{team.id}")
    assert response.status_code == HTTPStatus.OK
    assert response.json()["name"] == team.name


def test_get_team_not_found(client: TestClient, account: Account):
    url = "/v2/teams/doesnotexist"
    response = client.get(url, headers=_authorization(account))
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_get_private_team_without_access(
    client: TestClient,
    create_team: Callable[..., Team],
):
    """Anonymous visitors cannot retrieve a private team"""
    private_team = create_team(name="private", is_private=True)
    response = client.get(f"/v2/teams/{private_team.name}")
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_create_team(client: TestClient, account: Account, dbsession: OrmSession):
    response = client.post(
        "/v2/teams",
        headers=_authorization(account),
        json={"name": "newteam", "is_private": True},
    )
    assert response.status_code == HTTPStatus.OK

    response_json = response.json()
    assert response_json["name"] == "newteam"
    assert response_json["is_private"] is True
    assert response_json["id"] is not None

    assert db_team.get_team_or_none(dbsession, "newteam") is not None


def test_update_team(
    client: TestClient, account: Account, team: Team, dbsession: OrmSession
):
    original_name = team.name
    response = client.patch(
        f"/v2/teams/{team.name}",
        headers=_authorization(account),
        json={"name": "newkiwix", "is_private": True},
    )
    assert response.status_code == HTTPStatus.NO_CONTENT

    updated = db_team.get_team_or_none(dbsession, "newkiwix")
    assert updated is not None
    assert updated.is_private is True
    assert db_team.get_team_or_none(dbsession, original_name) is None


def test_get_team_history(
    client: TestClient,
    account: Account,
    create_team: Callable[..., Team],
    dbsession: OrmSession,
):
    """An account with access can list a team's history"""
    team = create_team(name="wikimedia")
    db_team.create_team_history_entry(dbsession, team, account.id, comment="first")
    db_team.create_team_history_entry(dbsession, team, account.id, comment="second")
    dbsession.flush()

    response = client.get(
        f"/v2/teams/{team.name}/history", headers=_authorization(account)
    )
    assert response.status_code == HTTPStatus.OK

    response_json = response.json()
    assert response_json["meta"]["count"] == 2
    assert len(response_json["items"]) == 2
    assert {item["comment"] for item in response_json["items"]} == {"first", "second"}


def test_get_team_history_pagination(
    client: TestClient,
    account: Account,
    create_team: Callable[..., Team],
    dbsession: OrmSession,
):
    team = create_team(name="wikimedia")
    for i in range(5):
        db_team.create_team_history_entry(dbsession, team, account.id, comment=f"{i}")
    dbsession.flush()

    response = client.get(
        f"/v2/teams/{team.name}/history?limit=2&skip=0",
        headers=_authorization(account),
    )
    assert response.status_code == HTTPStatus.OK
    response_json = response.json()
    assert response_json["meta"]["count"] == 5
    assert len(response_json["items"]) == 2


def test_get_team_history_without_access(
    client: TestClient,
    create_team: Callable[..., Team],
):
    """A team that cannot be accessed cannot have its history listed"""
    private_team = create_team(name="private", is_private=True)
    response = client.get(f"/v2/teams/{private_team.name}/history")
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_get_team_history_entry(
    client: TestClient,
    account: Account,
    create_team: Callable[..., Team],
    dbsession: OrmSession,
):
    team = create_team(name="wikimedia")
    entry = db_team.create_team_history_entry(
        dbsession, team, account.id, comment="first"
    )
    dbsession.flush()

    response = client.get(
        f"/v2/teams/{team.name}/history/{entry.id}",
        headers=_authorization(account),
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json()["id"] == str(entry.id)
    assert response.json()["comment"] == "first"


def test_get_team_history_entry_not_found(
    client: TestClient,
    account: Account,
    create_team: Callable[..., Team],
):
    team = create_team(name="wikimedia")
    response = client.get(
        f"/v2/teams/{team.name}/history/{uuid4()}",
        headers=_authorization(account),
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_revert_team(
    client: TestClient,
    account: Account,
    create_team: Callable[..., Team],
    dbsession: OrmSession,
):
    """Reverting a team restores its previous state and records a new entry"""
    team = create_team(name="wikimedia")
    entry = db_team.create_team_history_entry(
        dbsession, team, account.id, comment="first"
    )
    dbsession.flush()

    # move the team away from the state recorded in the history entry
    team.name = "openzim"
    team.is_private = True
    dbsession.add(team)
    dbsession.flush()

    response = client.patch(
        f"/v2/teams/{team.name}/revert/{entry.id}",
        headers=_authorization(account),
        json={"comment": "revert to wikimedia"},
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json()["name"] == "wikimedia"
    assert response.json()["is_private"] is False

    dbsession.refresh(team)
    assert team.name == "wikimedia"
    assert team.is_private is False

    history = db_team.get_team_history(dbsession, team_id=team.name, skip=0, limit=100)
    assert history.nb_records == 2
    assert history.records[0].comment == "revert to wikimedia"


def test_revert_team_name_conflict(
    client: TestClient,
    account: Account,
    create_team: Callable[..., Team],
    dbsession: OrmSession,
):
    """Reverting to a name already used by another team conflicts"""
    team = create_team(name="alpha")
    entry = db_team.create_team_history_entry(dbsession, team, account.id)
    dbsession.flush()

    # free up the "alpha" name and let another team claim it
    team.name = "beta"
    dbsession.add(team)
    dbsession.flush()
    create_team(name="alpha")

    response = client.patch(
        f"/v2/teams/{team.name}/revert/{entry.id}",
        headers=_authorization(account),
        json={},
    )
    assert response.status_code == HTTPStatus.CONFLICT


def test_revert_team_no_permission(
    client: TestClient,
    create_account: Callable[..., Account],
    create_team: Callable[..., Team],
    dbsession: OrmSession,
):
    account = create_account(permission=RoleEnum.GLOBAL_VIEWER)
    team = create_team(name="wikimedia")
    entry = db_team.create_team_history_entry(dbsession, team, account.id)
    dbsession.flush()

    response = client.patch(
        f"/v2/teams/{team.name}/revert/{entry.id}",
        headers=_authorization(account),
        json={},
    )
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_revert_team_not_found(
    client: TestClient,
    account: Account,
    create_team: Callable[..., Team],
):
    team = create_team(name="wikimedia")
    response = client.patch(
        f"/v2/teams/{team.name}/revert/{uuid4()}",
        headers=_authorization(account),
        json={},
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
