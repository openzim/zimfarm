import requests
import pytest


@pytest.fixture
def api_root():
    return 'https://farm.openzim.org/api'


@pytest.fixture
def access_token(api_root):
    print(api_root)
    response = requests.post(
        url=api_root+"/auth/authorize",
        headers={
            "username": "admin",
            "password": "admin_pass",
        },
    )
    return response.json()['access_token']


def test_get_schedule(api_root, access_token):
    response = requests.get(
        url=api_root+"/schedules/",
        headers={
            "token": access_token,
        },
    )

    response = response.json()
    assert response is not None

    items = response.get('items')
    assert isinstance(items, list)
