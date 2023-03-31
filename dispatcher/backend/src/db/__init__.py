import os

from sqlalchemy import create_engine

if not os.getenv("POSTGRES_URI"):
    raise EnvironmentError("Please set the POSTGRES_URI environment variable")

engine = create_engine(os.getenv("POSTGRES_URI"), echo=True)
