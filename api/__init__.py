from flask import Flask, g
from celery import Celery
from .database import SQLiteDB

db_path = '/Volumes/Data/zimfarm_test.sqlite'


def configure() -> (Flask, Celery):
    flask = Flask(__name__)
    celery = Celery(flask.name,
                    broker='pyamqp://celery:celery@localhost/celeryvhost',
                    backend='rpc://')
    celery.conf.update(flask.config)

    return flask, celery


def get_db():
    db = getattr(g, 'sqliteDB', None)
    if db is None:
        db = g.sqliteDB = SQLiteDB(db_path)
    return db

flask, celery = configure()

@flask.teardown_appcontext
def teardown_db(exception):
    db = getattr(g, 'sqliteDB', None)
    if db is not None:
        db.close()

from . import templates, task, database

if __name__ == "__main__":
    flask.run()
