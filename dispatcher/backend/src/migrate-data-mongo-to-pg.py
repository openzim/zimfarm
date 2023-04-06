import logging
from abc import ABC, abstractmethod
from json import loads
from typing import Any, Dict, List, Tuple

import sqlalchemy.orm as so
from bson.json_util import dumps
from pymongo.collection import Collection as BaseCollection

import common.mongo as mongo
import db.models as dbm
from db.engine import Session
from utils.keys_exporter import KeysExporter

logging.basicConfig(
    level=logging.DEBUG, format="[%(name)s - %(asctime)s: %(levelname)s] %(message)s"
)
logger = logging.getLogger("main")


def get_or_none(obj: Dict[str, Any], key: str) -> Any:
    return obj[key] if key in obj.keys() else None


def pre_checks_ok() -> bool:
    with Session() as session:
        return pre_checks_ok_internal(session)


def pre_checks_ok_internal(session: so.Session) -> bool:
    pre_checks_ok = True

    count = session.query(dbm.User).count()
    if count > 0:
        logger.warning(
            f"Please empty user table before migration ({count} records found)"
        )
        pre_checks_ok = False

    count = session.query(dbm.Sshkey).count()
    if count > 0:
        logger.warning(
            f"Please empty sshkey table before migration ({count} records found)"
        )
        pre_checks_ok = False

    count = session.query(dbm.Refreshtoken).count()
    if count > 0:
        logger.warning(
            "Please empty refresh tokens table before migration "
            f"({count} records found)"
        )
        pre_checks_ok = False

    return pre_checks_ok


class Migrator(ABC):
    _commit_every: int

    def __init__(self, commit_every: int = 1000) -> None:
        self._commit_every = commit_every

    @abstractmethod
    def get_object_name(self) -> str:
        pass

    @abstractmethod
    def get_mongo_collection(self) -> BaseCollection:
        pass

    @abstractmethod
    def get_sql_tables(self) -> List[Tuple[str, dbm.Base]]:
        pass

    @abstractmethod
    def get_expected_mongo_keys(self) -> List[str]:
        pass

    @abstractmethod
    def get_expected_mongo_json_objects(self) -> List[str]:
        pass

    @abstractmethod
    def migrate_one_doc(self, session: so.Session, mongo_obj) -> None:
        pass

    def get_next_mongo_doc(self):  # -> Generator[Any | None, None, None]:
        for mongoObj in self.get_mongo_collection().find({}, batch_size=100):
            yield mongoObj
        yield None

    def _key_starts_with(self, key, items):
        for item in items:
            if key.startswith(item):
                return True
        return False

    def check_one_doc(self, mongo_obj):
        existing_keys = KeysExporter.get_keys(mongo_obj)
        expected_keys = self.get_expected_mongo_keys()
        expected_json_objects = self.get_expected_mongo_json_objects()
        for existing_key in existing_keys:
            if existing_key not in expected_keys and not self._key_starts_with(
                existing_key, expected_json_objects
            ):
                raise Exception(
                    f"Unexpected key {existing_key} found in "
                    f"{self.get_object_name()} object id {str(mongo_obj['_id'])}"
                )

    def migrate(self) -> None:
        logger.info(
            f"\n##################\nMigrating {self.get_object_name()}"
            "\n##################"
        )
        count = self.get_mongo_collection().count_documents({})
        logger.info(f"{count} {self.get_object_name()} found in MongoDB")

        cnt = 1
        next_mongo_doc = self.get_next_mongo_doc()

        with Session() as session:
            while True:
                with session.begin():
                    while len(session.new) < 1000:
                        next_doc = next_mongo_doc.__next__()
                        if next_doc is None:
                            break
                        self.check_one_doc(next_doc)
                        self.migrate_one_doc(session, next_doc)

                if next_doc is None:
                    for sql_table in self.get_sql_tables():
                        count = session.query(sql_table[1]).count()
                        logger.info(
                            f"{count} {sql_table[0]} found in PG after migration"
                        )

                    break

                logger.info(f"Commiting after 1000 objects insert ({cnt})")
                cnt += 1


class UserMigrator(Migrator):
    def get_object_name(self) -> str:
        return "user"

    def get_mongo_collection(self) -> BaseCollection:
        return mongo.Users()

    def get_sql_tables(self) -> List[Tuple[str, dbm.Base]]:
        return [("user", dbm.User), ("sshkey", dbm.Sshkey)]

    def get_expected_mongo_keys(self) -> List[str]:
        return [
            "_id",
            "username",
            "email",
            "password_hash",
            "ssh_keys",
            "ssh_keys.*.name",
            "ssh_keys.*.fingerprint",
            "ssh_keys.*.type",
            "ssh_keys.*.key",
            "ssh_keys.*.added",
            "ssh_keys.*.last_used",
            "ssh_keys.*.pkcs8_key",
        ]

    def get_expected_mongo_json_objects(self) -> List[str]:
        return [
            "scope",
        ]

    def migrate_one_doc(self, session: so.Session, mongo_obj) -> None:
        orm_user = dbm.User(
            mongo_val=loads(dumps(mongo_obj)),
            mongo_id=str(mongo_obj["_id"]),
            username=mongo_obj["username"],
            email=get_or_none(mongo_obj, "email"),
            password_hash=mongo_obj["password_hash"],
            scope=mongo_obj["scope"],
        )
        session.add(orm_user)
        for ssh_key in get_or_none(mongo_obj, "ssh_keys") or []:
            orm_user.ssh_keys.append(
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


class RefreshTokenMigrator(Migrator):
    cache: Dict[str, str] = {}

    def get_object_name(self) -> str:
        return "refresh token"

    def get_mongo_collection(self) -> BaseCollection:
        return mongo.RefreshTokens()

    def get_sql_tables(self) -> List[Tuple[str, dbm.Base]]:
        return [("refresh token", dbm.Refreshtoken)]

    def get_expected_mongo_keys(self) -> List[str]:
        return [
            "_id",
            "user_id",
            "username",
            "token",
            "expire_time",
        ]

    def get_expected_mongo_json_objects(self) -> List[str]:
        return []

    def migrate_one_doc(self, session: so.Session, mongo_obj) -> None:
        if "user_id" in mongo_obj:
            mongo_user_id = str(mongo_obj["user_id"])
            cache_key = f"id_{mongo_user_id}"
            if cache_key in self.cache:
                user_id = self.cache[cache_key]
            else:
                user_id = (
                    session.query(dbm.User.id)
                    .where(dbm.User.mongo_id == mongo_user_id)
                    .scalar()
                )
                if user_id:
                    self.cache[cache_key] = user_id
                else:
                    raise Exception(
                        f"Impossible to find user with ID {mongo_user_id} for refresh "
                        f"token {str(mongo_obj['_id'])}"
                    )
        else:
            mongo_user_name = mongo_obj["username"]
            cache_key = f"name_{mongo_user_name}"
            if cache_key in self.cache:
                user_id = self.cache[cache_key]
            else:
                user_id = (
                    session.query(dbm.User.id)
                    .where(dbm.User.username == mongo_user_name)
                    .scalar()
                )
                if user_id:
                    self.cache[cache_key] = user_id
                else:
                    raise Exception(
                        f"Impossible to find user with name {mongo_user_name} for "
                        f"refresh token {str(mongo_obj['_id'])}"
                    )

        orm_refresh_token = dbm.Refreshtoken(
            mongo_val=loads(dumps(mongo_obj)),
            mongo_id=str(mongo_obj["_id"]),
            token=mongo_obj["token"],
            expire_time=mongo_obj["expire_time"],
        )
        orm_refresh_token.user_id = user_id
        session.add(orm_refresh_token)


def main():
    logger.info("Migrating data from Mongo to PostgreSQL")

    if not pre_checks_ok():
        logger.error("Please fix warnings before proceeding with the migration")
        return

    UserMigrator().migrate()

    RefreshTokenMigrator().migrate()


if __name__ == "__main__":
    main()
