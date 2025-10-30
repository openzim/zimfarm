from http import HTTPStatus

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.sql import text

from healthcheck.constants import ZIMFARM_DATABASE_URL as DATABASE_URL
from healthcheck.status import Result
from healthcheck.status import status_logger as logger

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)
async_session = async_sessionmaker(engine, expire_on_commit=False)


class DatabaseConnectionInfo(BaseModel):
    status: str
    version: str


async def check_database_connection() -> Result[DatabaseConnectionInfo]:
    """Check if we can connect to the database and run a simple query."""
    try:
        async with async_session() as session:
            (await session.execute(text("SELECT 1"))).scalar_one_or_none()

            version = (await session.execute(text("SHOW server_version"))).scalar_one()

            logger.debug(
                f"Database connection successful, version: {version}",
                extra={"checkname": "zimfarm-database-connection"},
            )

            return Result(
                success=True,
                status_code=HTTPStatus.OK,
                data=DatabaseConnectionInfo(
                    status="online",
                    version=version,
                ),
            )
    except Exception:
        logger.exception(
            "Database connection check failed",
            extra={"checkname": "zimfarm-database-connection"},
        )
        return Result(
            success=False,
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            data=DatabaseConnectionInfo(
                status="offline",
                version="unknown",
            ),
        )
