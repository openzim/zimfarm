import pytest

from bson import ObjectId

from main import flask
from pymongo import MongoClient
from pymongo.database import Database
from utils.token import AccessControl


@pytest.fixture(scope='session')
def client():
    flask.testing = True
    client = flask.test_client()
    yield client


@pytest.fixture(scope='session')
def access_token():
    token = AccessControl(ObjectId(), 'username', {}).encode()
    yield 'Bearer {}'.format(token)


@pytest.fixture(scope='session')
def database() -> Database:
    yield MongoClient('localhost', 27017)['Zimfarm']
