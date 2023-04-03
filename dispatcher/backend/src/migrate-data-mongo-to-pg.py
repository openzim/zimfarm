import contextlib
import logging
from json import loads
from typing import Any, Dict

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
        logger.warn(f"Please empty user table before migration ({count} records found)")
        pre_checks_ok = False

    count = session.query(dbm.Sshkey).count()
    if count > 0:
        logger.warn(
            f"Please empty sshkey table before migration ({count} records found)"
        )
        pre_checks_ok = False

    return pre_checks_ok


def migrate_users(session: so.Session):
    logger.info("\n##################\nMigrating users\n##################")
    count = mongo.Users().count_documents({})
    logger.info(f"{count} users found in MongoDB")

    for mongoUser in mongo.Users().find({}, batch_size=100):
        if len(session.new) > 1000:
            logger.info("Commiting after 1000 objects insert")
            session.commit()

        pgmUser = dbm.User(
            mongo_val=loads(dumps(mongoUser)),
            mongo_id=mongoUser["_id"].value,
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

    count = session.query(dbm.User).count()
    logger.info(f"{count} User found in PG after migration")

    count = session.query(dbm.Sshkey).count()
    logger.info(f"{count} Sshkey found in PG after migration")
    # logger.info(f"{len(session.new)} objects to insert")
    #     print(user["_id"])


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
        migrate_users(session)
        migrate_schedules(session)


if __name__ == "__main__":
    main()
