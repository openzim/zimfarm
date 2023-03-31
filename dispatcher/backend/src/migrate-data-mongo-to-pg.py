import logging
from json import loads
from typing import Any, Dict

import sqlalchemy as sa
import sqlalchemy.orm as so
from bson.json_util import dumps

import common.mongo as mongo
import db.models as pgm
from db.engine import engine

logging.basicConfig(
    level=logging.DEBUG, format="[%(name)s - %(asctime)s: %(levelname)s] %(message)s"
)
logger = logging.getLogger("main")


def get_or_none(obj: Dict[str, Any], key: str) -> Any:
    return obj[key] if key in obj.keys() else None


def migrate_users(session):
    logger.info("\n##################\nMigrating users\n##################")
    count = mongo.Users().count_documents({})
    logger.info(f"{count} users found in MongoDB")

    count = session.query(pgm.User).count()
    logger.info(f"{count} User found in PG before migration")

    count = session.query(pgm.Sshkey).count()
    logger.info(f"{count} Sshkey found in PG before migration")

    for mongoUser in mongo.Users().find({}, batch_size=100):
        if len(session.new) > 1000:
            logger.info("Commiting after 1000 objects insert")
            session.commit()

        pgmUser = pgm.User(
            mongo_val=loads(dumps(mongoUser)),
            username=mongoUser["username"],
            email=get_or_none(mongoUser, "email"),
            password_hash=mongoUser["password_hash"],
            scope=mongoUser["scope"],
        )
        session.add(pgmUser)
        for ssh_key in get_or_none(mongoUser, "ssh_keys") or []:
            pgmUser.ssh_keys.append(
                pgm.Sshkey(
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

    count = session.query(pgm.User).count()
    logger.info(f"{count} User found in PG after migration")

    count = session.query(pgm.Sshkey).count()
    logger.info(f"{count} Sshkey found in PG after migration")
    # logger.info(f"{len(session.new)} objects to insert")
    #     print(user["_id"])


def main():
    logger.info("Migrating data from Mongo to PostgreSQL")

    with so.Session(engine) as session:
        migrate_users(session)


if __name__ == "__main__":
    main()
