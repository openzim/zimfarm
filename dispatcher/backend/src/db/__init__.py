import os

from bson.json_util import dumps, loads
from sqlalchemy import SelectBase, create_engine, func, select
from sqlalchemy.orm import Session as OrmSession
from sqlalchemy.orm import sessionmaker

if not os.getenv("POSTGRES_URI"):
    raise EnvironmentError("Please set the POSTGRES_URI environment variable")

if (
    os.getenv("POSTGRES_URI") == "nodb"
):  # this is a hack for cases where we do not need the DB, e.g. unit tests
    Session = None
else:
    Session = sessionmaker(
        bind=create_engine(
            os.getenv("POSTGRES_URI"),
            echo=False,
            json_serializer=dumps,  # use bson serializer to handle ObjectId + datetime
            json_deserializer=loads,  # use bson deserializer for same reason
        )
    )


def dbsession(func):
    """Decorator to create an SQLAlchemy ORM session object and wrap the function
    inside the session. A `session` argument is automatically set. Commit is
    automatically performed when the function finish (and before returning to
    the caller). Should any exception arise, rollback of the transaction is also
    automatic.
    """

    def inner(*args, **kwargs):
        with Session.begin() as session:
            kwargs["session"] = session
            return func(*args, **kwargs)

    return inner


def count_from_stmt(session: OrmSession, stmt: SelectBase) -> int:
    """Count all records returned by any statement `stmt` passed as parameter"""
    return session.execute(
        select(func.count()).select_from(stmt.subquery())
    ).scalar_one()
