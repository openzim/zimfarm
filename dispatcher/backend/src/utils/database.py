import logging
import os

import sqlalchemy.orm as so
from alembic import config, script
from alembic.runtime import migration
from werkzeug.security import generate_password_hash

import db.models as dbm
from common import mongo
from common.roles import ROLES
from db.session import dbsession

logger = logging.getLogger(__name__)


class Initializer:
    @staticmethod
    def initialize():
        print("Running pre-start initialization...")
        mongo.Users().initialize()
        mongo.Schedules().initialize()
        mongo.Tasks().initialize()
        mongo.RequestedTasks().initialize()

    @staticmethod
    @dbsession
    def check_if_schema_is_up_to_date(session: so.Session):
        logger.info("Checking database schema")
        cfg = config.Config("alembic.ini")
        directory = script.ScriptDirectory.from_config(cfg)
        context = migration.MigrationContext.configure(session.connection())
        current_heads = set(context.get_current_heads())
        directory_heads = set(directory.get_heads())
        logger.info(f"current heads: {current_heads}")
        logger.info(f"directory heads: {directory_heads}")
        if current_heads != directory_heads:
            raise EnvironmentError(
                "Database schema is not up to date, please update schema first"
            )
        logger.info("Database is up to date")

    @staticmethod
    @dbsession
    def create_initial_user(session: so.Session):
        username = os.getenv("INIT_USERNAME", "admin")
        password = os.getenv("INIT_PASSWORD", "admin_pass")

        count = session.query(dbm.User).count()
        if count == 0:
            print(f"creating initial user `{username}`")
            orm_user = dbm.User(
                mongo_val=None,
                mongo_id=None,
                username=username,
                email=None,
                password_hash=generate_password_hash(password),
                scope=ROLES.get("admin"),
            )
            session.add(orm_user)
