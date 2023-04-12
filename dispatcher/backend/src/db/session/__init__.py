import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

if not os.getenv("POSTGRES_URI"):
    raise EnvironmentError("Please set the POSTGRES_URI environment variable")

__engine = create_engine(os.getenv("POSTGRES_URI"), echo=False)

Session = sessionmaker(__engine)


def dbsession(func):
    def inner(*args, **kwargs):
        with Session.begin() as session:
            kwargs["session"] = session
            return func(*args, **kwargs)

    return inner
