import contextlib
import logging
from json import loads
from typing import Any, Dict
from uuid import UUID

import sqlalchemy as sa
import sqlalchemy.orm as so
from bson.json_util import dumps

import common.mongo as mongo
import db.models as dbm
from db.engine import Session

logging.basicConfig(
    level=logging.DEBUG, format="[%(name)s - %(asctime)s: %(levelname)s] %(message)s"
)
logger = logging.getLogger("main")


def get_or_none(obj: Dict[str, Any], key: str) -> Any:
    return obj[key] if key in obj.keys() else None


def pre_checks_ok(session: so.Session) -> bool:
    pre_checks_ok = True

    count = session.query(dbm.User).count()
    if count > 0:
        logger.warning(
            f"Please empty user table before migration ({count} records found)"
        )
        pre_checks_ok = False

    # count = session.query(dbm.Sshkey).count()
    # if count > 0:
    #     logger.warning(
    #         f"Please empty sshkey table before migration ({count} records found)"
    #     )
    #     pre_checks_ok = False

    count = session.query(dbm.Refreshtoken).count()
    if count > 0:
        logger.warning(
            f"Please empty refresh tokens table before migration ({count} records found)"
        )
        pre_checks_ok = False

    return pre_checks_ok


def migrate_users():
    logger.info("\n##################\nMigrating users\n##################")
    count = mongo.Users().count_documents({})
    logger.info(f"{count} users found in MongoDB")

    cnt = 1
    session: so.Session = Session().begin().session
    for mongoUser in mongo.Users().find({}, batch_size=100):
        if len(session.new) > 1000:
            logger.info(f"Commiting after 1000 objects insert ({cnt})")
            cnt += 1
            session.commit()
            session = Session().begin().session

        pgmUser = dbm.User(
            mongo_val=loads(dumps(mongoUser)),
            mongo_id=str(mongoUser["_id"]),
            username=mongoUser["username"],
            email=get_or_none(mongoUser, "email"),
            password_hash=mongoUser["password_hash"],
            scope=mongoUser["scope"],
        )
        session.add(pgmUser)
        for ssh_key in get_or_none(mongoUser, "ssh_keys") or []:
            pgmUser.ssh_keys.append(
                dbm.Sshkey(
                    mongo_val=loads(dumps(ssh_key)),
                    name=get_or_none(ssh_key, "name"),
                    fingerprint=get_or_none(ssh_key, "fingerprint"),
                    type=get_or_none(ssh_key, "type"),
                    key=get_or_none(ssh_key, "key"),
                    added=get_or_none(ssh_key, "added"),
                    last_used=get_or_none(ssh_key, "last_used"),
                    pkcs8_key=get_or_none(ssh_key, "pkcs8_key"),
                )
            )

    session.commit()
    session = Session().begin().session

    count = session.query(dbm.User).count()
    logger.info(f"{count} User found in PG after migration")

    count = session.query(dbm.Sshkey).count()
    logger.info(f"{count} Sshkey found in PG after migration")
    # logger.info(f"{len(session.new)} objects to insert")
    #     print(user["_id"])


def migrate_refresh_tokens():
    logger.info("\n##################\nMigrating refresh tokens\n##################")
    count = mongo.RefreshTokens().count_documents({})
    logger.info(f"{count} refresh tokens found in MongoDB")

    cache: Dict[str, str] = {}
    cnt = 1
    session: so.Session = Session().begin().session
    for mongoRefreshToken in mongo.RefreshTokens().find({}, batch_size=100):
        if len(session.new) > 1000:
            logger.info(f"Commiting after 1000 objects insert ({cnt})")
            cnt += 1
            session.commit()
            session = Session().begin().session

        if "user_id" in mongoRefreshToken:
            mongo_user_id = str(mongoRefreshToken["user_id"])
            cache_key = f"id_{mongo_user_id}"
            if cache_key in cache:
                user_id = cache[cache_key]
            else:
                user_id = (
                    session.query(dbm.User.id)
                    .where(dbm.User.mongo_id == mongo_user_id)
                    .scalar()
                )
                if user_id:
                    cache[cache_key] = user_id
                else:
                    logger.error(
                        f"Impossible to find user {mongo_user_id} for refresh token {str(mongoRefreshToken['_id'])}"
                    )
        else:
            mongo_user_name = mongoRefreshToken["username"]
            cache_key = f"name_{mongo_user_name}"
            if cache_key in cache:
                user_id = cache[cache_key]
            else:
                user_id = (
                    session.query(dbm.User.id)
                    .where(dbm.User.username == mongo_user_name)
                    .scalar()
                )
                if user_id:
                    cache[cache_key] = user_id
                else:
                    logger.error(
                        f"Impossible to find user {mongo_user_name} for refresh token {str(mongoRefreshToken['_id'])}"
                    )

        pgmRefreshToken = dbm.Refreshtoken(
            mongo_val=loads(dumps(mongoRefreshToken)),
            mongo_id=str(mongoRefreshToken["_id"]),
            token=mongoRefreshToken["token"],
            expire_time=mongoRefreshToken["expire_time"],
        )
        pgmRefreshToken.user_id = user_id
        session.add(pgmRefreshToken)

    session.commit()
    session = Session().begin().session

    count = session.query(dbm.Refreshtoken).count()
    logger.info(f"{count} refresh tokens found in PG after migration")


def migrate_schedules(session):
    logger.info("\n##################\nMigrating schedules\n##################")
    count = mongo.Schedules().count_documents({})
    logger.info(f"{count} schedules found in MongoDB")

    # count = session.query(pgm.User).count()
    # logger.info(f"{count} User found in PG before migration")

    # count = session.query(pgm.Sshkey).count()
    # logger.info(f"{count} Sshkey found in PG before migration")

    # i = 0
    # for mongoTask in mongo.Schedules().find({}, batch_size=100):
    #     i += 1
    #     if i >= 1000:
    #         break

    # i = 0
    # for mongoTaskId in mongo.Schedules().find(
    #     {}, projection={"_id": 1}, batch_size=100
    # ):
    #     i += 1
    #     mongoTask = mongo.Schedules().find_one({"_id": mongoTaskId["_id"]})
    #     if i >= 1000:
    #         break
    # if len(session.new) > 1000:
    #     logger.info("Commiting after 1000 objects insert")
    #     session.commit()

    # logger.info(f"Done {i}")


def main():
    logger.info("Migrating data from Mongo to PostgreSQL")

    with Session.begin() as session:
        if not pre_checks_ok(session):
            logger.error("Please fix warnings before proceeding with the migration")
            return

    migrate_users()
    # migrate_schedules(session)

    migrate_refresh_tokens()


if __name__ == "__main__":
    main()
