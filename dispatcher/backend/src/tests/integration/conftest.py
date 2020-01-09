import os

import pytest
from bson import ObjectId
from pymongo import MongoClient
from pymongo.database import Database
from flask.testing import FlaskClient

from main import application as app
from common import mongo
from common.roles import ROLES
from routes import API_PATH
from utils.token import LoadedAccessToken

# monley-patching FlaskClient to prefix test URLs with proper API_PATH
original_get = FlaskClient.get


def rewritten_get(self, url, *args, **kwargs):
    url = f"{API_PATH}{url}"
    return original_get(self, url, *args, **kwargs)


original_post = FlaskClient.post


def rewritten_post(self, url, *args, **kwargs):
    url = f"{API_PATH}{url}"
    return original_post(self, url, *args, **kwargs)


original_put = FlaskClient.put


def rewritten_put(self, url, *args, **kwargs):
    url = f"{API_PATH}{url}"
    return original_put(self, url, *args, **kwargs)


original_patch = FlaskClient.patch


def rewritten_patch(self, url, *args, **kwargs):
    url = f"{API_PATH}{url}"
    return original_patch(self, url, *args, **kwargs)


original_delete = FlaskClient.delete


def rewritten_delete(self, url, *args, **kwargs):
    url = f"{API_PATH}{url}"
    return original_delete(self, url, *args, **kwargs)


FlaskClient.get = rewritten_get
FlaskClient.post = rewritten_post
FlaskClient.put = rewritten_put
FlaskClient.patch = rewritten_patch
FlaskClient.delete = rewritten_delete


@pytest.fixture(scope="session")
def client():
    app.testing = True
    client = app.test_client()
    yield client


@pytest.fixture(scope="session")
def access_token():
    token = LoadedAccessToken(ObjectId(), "username", ROLES.get("admin")).encode()
    yield "Bearer {}".format(token)


@pytest.fixture(scope="session")
def database() -> Database:
    client = MongoClient(os.getenv("MONGO_HOSTNAME"), 27017)
    database = client["Zimfarm"]
    mongo.Tasks(database=database).initialize()
    yield database
