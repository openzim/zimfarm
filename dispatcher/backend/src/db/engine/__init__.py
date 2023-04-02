import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

if not os.getenv("POSTGRES_URI"):
    raise EnvironmentError("Please set the POSTGRES_URI environment variable")

_engine = create_engine(os.getenv("POSTGRES_URI"), echo=True)

Session = sessionmaker(_engine)
