import pytest

from bson import ObjectId

from main import flask
import mongo
from utils.token import AccessControl


@pytest.fixture
def client():
    flask.testing = True
    client = flask.test_client()
    yield client


@pytest.fixture
def access_token():
    token = AccessControl(ObjectId(), 'username', {}).encode()
    yield 'Bearer {}'.format(token)
