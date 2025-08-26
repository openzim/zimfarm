import subprocess

from alembic import config, script
from alembic.runtime import migration
from werkzeug.security import generate_password_hash

from zimfarm_backend import logger
from zimfarm_backend.common.constants import BASE_DIR, getenv
from zimfarm_backend.common.roles import ROLES
from zimfarm_backend.db import Session
from zimfarm_backend.db.models import User


def check_if_schema_is_up_to_date():
    with Session.begin() as session:
        logger.info("Checking database schema")
        cfg = config.Config(BASE_DIR / "alembic.ini")
        cfg.set_main_option("script_location", "zimfarm_backend:migrations")
        directory = script.ScriptDirectory.from_config(cfg)
        context = migration.MigrationContext.configure(session.connection())
        current_heads = set(context.get_current_heads())
        directory_heads = set(directory.get_heads())
        logger.info(f"current heads: {current_heads}")
        logger.info(f"directory heads: {directory_heads}")
        if current_heads != directory_heads:
            raise ValueError(
                "Database schema is not up to date, please update schema first"
            )
        logger.info("Database is up to date")


def create_initial_user():
    with Session.begin() as session:
        username = getenv("INIT_USERNAME", default="admin")
        password = getenv("INIT_PASSWORD", default="admin_pass")

        count = session.query(User).count()
        if count == 0:
            logger.info(f"creating initial user `{username}`")
            orm_user = User(
                username=username,
                email=None,
                password_hash=generate_password_hash(password),
                scope=ROLES.get("admin"),
                deleted=False,
            )
            session.add(orm_user)
        else:
            logger.info(f"user {username} already exists")


def upgrade_db_schema():
    """Checks if Alembic schema has been applied to the DB"""
    logger.info(f"Upgrading database schema with config in {BASE_DIR}")
    subprocess.check_output(args=["alembic", "upgrade", "head"], cwd=BASE_DIR)
