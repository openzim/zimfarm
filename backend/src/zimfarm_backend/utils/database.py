import subprocess

from alembic import config, script
from alembic.runtime import migration
from werkzeug.security import generate_password_hash

from zimfarm_backend import logger
from zimfarm_backend.common.constants import BASE_DIR, getenv
from zimfarm_backend.db import Session
from zimfarm_backend.db.models import User
from zimfarm_backend.db.offliner import get_all_offliners


def check_if_schema_is_up_to_date() -> bool:
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
            logger.warning(
                "Database schema is not up to date, please update schema first"
            )
            return False
        logger.info("Database is up to date")
        return True


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
                scope=None,
                role="admin",
                deleted=False,
            )
            session.add(orm_user)
        else:
            logger.info(f"user {username} already exists")


def upgrade_db_schema():
    """Checks if Alembic schema has been applied to the DB"""
    logger.info(f"Upgrading database schema with config in {BASE_DIR}")
    subprocess.check_output(args=["alembic", "upgrade", "head"], cwd=BASE_DIR)


def load_offliners():
    with Session.begin() as session:
        get_all_offliners(session)
