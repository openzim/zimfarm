import os

import pytest
from bson import ObjectId
from pymongo import MongoClient
from pymongo.database import Database

from common import mongo
from main import flask
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
    client = MongoClient(os.getenv('MONGO_HOSTNAME'), 27017)
    database = client['Zimfarm']
    mongo.Tasks(database=database).initialize()
    yield database
