import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple
from uuid import UUID

import sqlalchemy as sa
import sqlalchemy.orm as so
from pymongo.collection import Collection as BaseCollection

import common.mongo as mongo
import db.models as dbm
from db import Session, dbsession
from routes.utils import raise_if_none
from utils.database import Initializer

logging.basicConfig(
    level=logging.DEBUG, format="[%(name)s - %(asctime)s: %(levelname)s] %(message)s"
)
logger = logging.getLogger("main")


def get_or_none(obj: Dict[str, Any], key: str) -> Any:
    return obj[key] if key in obj.keys() else None


def set_null_dict(obj: Dict[str, Any]) -> Dict[str, Any]:
    return None if obj == {} else obj


class KeysExporter:
    @staticmethod
    def _get_keys_int(obj, curPrefix):
        if isinstance(obj, Dict):
            for k, v in obj.items():
                yield f"{curPrefix}{k}"
                yield from KeysExporter._get_keys_int(v, f"{curPrefix}{k}.")
        elif isinstance(obj, List):
            for v in obj:
                yield from KeysExporter._get_keys_int(v, f"{curPrefix}*.")

    @staticmethod
    def get_keys(obj) -> List[str]:
        return set(KeysExporter._get_keys_int(obj, ""))


class KeyNotFoundException(Exception):
    pass


class MigrationCache:
    cache: Dict[str, UUID] = {}

    def _get_inner(
        self, session: so.Session, cache_key: str, stmt: sa.Select[Tuple], errorMsg: str
    ) -> UUID:
        if cache_key not in self.cache:
            pg_id = session.execute(stmt).scalar_one_or_none()
            if pg_id is None:
                self.cache[cache_key] = None
                raise KeyNotFoundException(errorMsg)
            self.cache[cache_key] = pg_id
        return self.cache[cache_key]

    def get_pg_user_id_by_mongo_user_id(
        self, session: so.Session, mongo_user_id: str, used_by_str: str
    ) -> UUID:
        return self._get_inner(
            session=session,
            cache_key=f"user_id_{mongo_user_id}",
            stmt=sa.select(dbm.User.id).where(dbm.User.mongo_id == mongo_user_id),
            errorMsg=(
                f"Impossible to find user with ID {mongo_user_id}"
                f" used by {used_by_str}"
            ),
        )

    def get_pg_user_id_by_username(
        self, session: so.Session, username: str, used_by_str: str
    ) -> UUID:
        return self._get_inner(
            session=session,
            cache_key=f"user_name_{username}",
            stmt=sa.select(dbm.User.id).where(dbm.User.username == username),
            errorMsg=(
                f"Impossible to find user with name {username}"
                f" used by {used_by_str}"
            ),
        )

    def get_pg_schedule_id_by_schedulename(
        self, session: so.Session, schedulename: str, used_by_str: str
    ) -> UUID:
        return self._get_inner(
            session=session,
            cache_key=f"schedule_name_{schedulename}",
            stmt=sa.select(dbm.Schedule.id).where(dbm.Schedule.name == schedulename),
            errorMsg=(
                f"Impossible to find schedule with name {schedulename}"
                f" used by {used_by_str}"
            ),
        )

    def get_pg_worker_id_by_workername(
        self, session: so.Session, workername: str, used_by_str: str
    ) -> UUID:
        return self._get_inner(
            session=session,
            cache_key=f"worker_name_{workername}",
            stmt=sa.select(dbm.Worker.id).where(dbm.Worker.name == workername),
            errorMsg=(
                f"Impossible to find worker with name {workername}"
                f" used by {used_by_str}"
            ),
        )


class Migrator(ABC):
    _commit_every: int
    _cache: MigrationCache

    def __init__(self, cache: MigrationCache, commit_every: int = 1000) -> None:
        self._commit_every = commit_every
        self._cache = cache

    @abstractmethod
    def get_mongo_object_name(self) -> str:
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
    def migrate_one_doc_phase_1(self, session: so.Session, mongo_obj) -> None:
        pass

    @abstractmethod
    def has_migrate_phase_2(self) -> bool:
        pass

    @abstractmethod
    def migrate_one_doc_phase_2(self, session: so.Session, mongo_obj) -> None:
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
                    f"{self.get_mongo_object_name()} object id {str(mongo_obj['_id'])}"
                )

    def migrate_phase_1(self) -> None:
        logger.info(
            f"\n##################\nMigrating phase 1 of {self.get_mongo_object_name()}"
            " documents\n##################"
        )
        count = self.get_mongo_collection().count_documents({})
        logger.info(f"{count} {self.get_mongo_object_name()} found in MongoDB")

        cnt = 1
        next_mongo_doc = self.get_next_mongo_doc()

        while True:
            with Session.begin() as session:
                for _ in range(self._commit_every):
                    next_doc = next_mongo_doc.__next__()
                    if next_doc is None:
                        break
                    self.check_one_doc(next_doc)
                    self.migrate_one_doc_phase_1(session, next_doc)

            if next_doc is None:
                for sql_table in self.get_sql_tables():
                    count = session.query(sql_table[1]).count()
                    logger.info(f"{count} {sql_table[0]} found in PG after migration")

                break

            logger.info(
                f"Commiting after {self._commit_every} documents processed ({cnt})"
            )
            cnt += 1

    def migrate_phase_2(self) -> None:
        logger.info(
            f"\n##################\nMigrating phase 2 of {self.get_mongo_object_name()}"
            " documents\n##################"
        )

        cnt = 1
        next_mongo_doc = self.get_next_mongo_doc()

        with Session() as session:
            while True:
                with session.begin():
                    for _ in range(self._commit_every):
                        next_doc = next_mongo_doc.__next__()
                        if next_doc is None:
                            break
                        self.migrate_one_doc_phase_2(session, next_doc)

                if next_doc is None:
                    for sql_table in self.get_sql_tables():
                        count = session.query(sql_table[1]).count()
                        logger.info(
                            f"{count} {sql_table[0]} found in PG after migration"
                        )

                    break

                logger.info(
                    f"Commiting after {self._commit_every} documents processed ({cnt})"
                )
                cnt += 1


@dbsession
def tables_are_empty(migrators: List[Migrator], session: so.Session) -> bool:
    tables_are_empty = True

    for migrator in migrators:
        for table_def in migrator.get_sql_tables():
            count = session.query(table_def[1]).count()
            if count > 0:
                logger.warning(
                    f"Please empty {table_def[0]} table before migration ({count}"
                    " records found)"
                )
                tables_are_empty = False

    return tables_are_empty


class UserMigrator(Migrator):
    def get_mongo_object_name(self) -> str:
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

    def migrate_one_doc_phase_1(self, session: so.Session, mongo_obj) -> None:
        orm_user = dbm.User(
            mongo_val=mongo_obj,
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
                    mongo_val=ssh_key,
                    name=get_or_none(ssh_key, "name"),
                    fingerprint=get_or_none(ssh_key, "fingerprint"),
                    type=get_or_none(ssh_key, "type"),
                    key=get_or_none(ssh_key, "key"),
                    added=get_or_none(ssh_key, "added"),
                    last_used=get_or_none(ssh_key, "last_used"),
                    pkcs8_key=get_or_none(ssh_key, "pkcs8_key"),
                )
            )

    def has_migrate_phase_2(self) -> bool:
        return False

    def migrate_one_doc_phase_2(self, session: so.Session, mongo_obj) -> None:
        pass


class RefreshTokenMigrator(Migrator):
    cache: Dict[str, str] = {}

    def get_mongo_object_name(self) -> str:
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

    def migrate_one_doc_phase_1(self, session: so.Session, mongo_obj) -> None:
        if "user_id" in mongo_obj:
            user_id = self._cache.get_pg_user_id_by_mongo_user_id(
                session=session,
                mongo_user_id=str(mongo_obj["user_id"]),
                used_by_str=(
                    f"property 'user_id' in refresh token {str(mongo_obj['_id'])}"
                ),
            )
        else:
            user_id = self._cache.get_pg_user_id_by_username(
                session=session,
                username=mongo_obj["username"],
                used_by_str=(
                    f"property 'username' in refresh token {str(mongo_obj['_id'])}"
                ),
            )

        orm_refresh_token = dbm.Refreshtoken(
            mongo_val=mongo_obj,
            mongo_id=str(mongo_obj["_id"]),
            token=mongo_obj["token"],
            expire_time=mongo_obj["expire_time"],
        )
        # we set the user_id explicitely (instead of adding the refresh token to the
        # list of current user refresh tokens) since it allows to not keep in memory
        # all users (no big deal for now) + all refresh tokens (this would consume a
        # lot of memory)
        orm_refresh_token.user_id = user_id
        session.add(orm_refresh_token)

    def has_migrate_phase_2(self) -> bool:
        return False

    def migrate_one_doc_phase_2(self, session: so.Session, mongo_obj) -> None:
        pass


class WorkerMigrator(Migrator):
    cache: Dict[str, str] = {}

    def get_mongo_object_name(self) -> str:
        return "worker"

    def get_mongo_collection(self) -> BaseCollection:
        return mongo.Workers()

    def get_sql_tables(self) -> List[Tuple[str, dbm.Base]]:
        return [("worker", dbm.Worker)]

    def get_expected_mongo_keys(self) -> List[str]:
        return [
            "_id",
            "name",
            "username",
            "selfish",
            "resources",
            "resources.cpu",
            "resources.disk",
            "resources.memory",
            "offliners",
            "last_seen",
            "last_ip",
        ]

    def get_expected_mongo_json_objects(self) -> List[str]:
        return ["platforms"]

    def migrate_one_doc_phase_1(self, session: so.Session, mongo_obj) -> None:
        user_id = self._cache.get_pg_user_id_by_username(
            session=session,
            username=str(mongo_obj["username"]),
            used_by_str=(f"property 'username' in worker {str(mongo_obj['_id'])}"),
        )

        orm_worker = dbm.Worker(
            mongo_val=mongo_obj,
            mongo_id=str(mongo_obj["_id"]),
            name=mongo_obj["name"],
            selfish=mongo_obj["selfish"],
            cpu=mongo_obj["resources"]["cpu"],
            memory=mongo_obj["resources"]["memory"],
            disk=mongo_obj["resources"]["disk"],
            offliners=mongo_obj["offliners"],
            platforms=mongo_obj["platforms"],
            last_seen=mongo_obj["last_seen"],
            last_ip=mongo_obj["last_ip"],
        )
        orm_worker.user_id = user_id
        session.add(orm_worker)

    def has_migrate_phase_2(self) -> bool:
        return False

    def migrate_one_doc_phase_2(self, session: so.Session, mongo_obj) -> None:
        pass


class ScheduleMigrator(Migrator):
    def get_mongo_object_name(self) -> str:
        return "schedule"

    def get_mongo_collection(self) -> BaseCollection:
        return mongo.Schedules()

    def get_sql_tables(self) -> List[Tuple[str, dbm.Base]]:
        return [("schedule", dbm.Schedule), ("schedule_duration", dbm.ScheduleDuration)]

    def get_expected_mongo_keys(self) -> List[str]:
        return [
            "_id",
            "name",
            "category",
            "enabled",
            "language",
            "language.code",
            "language.name_native",
            "language.name_en",
            "periodicity",
            "tags",
        ]

    def get_expected_mongo_json_objects(self) -> List[str]:
        return ["config", "duration", "most_recent_task", "notification"]

    def migrate_one_doc_phase_1(self, session: so.Session, mongo_obj) -> None:
        schedule = dbm.Schedule(
            mongo_val=mongo_obj,
            mongo_id=str(mongo_obj["_id"]),
            name=mongo_obj["name"],
            category=mongo_obj["category"],
            config=mongo_obj["config"],
            enabled=mongo_obj["enabled"],
            language_code=mongo_obj["language"]["code"],
            language_name_native=mongo_obj["language"]["name_native"],
            language_name_en=mongo_obj["language"]["name_en"],
            tags=mongo_obj["tags"],
            periodicity=mongo_obj["periodicity"],
            notification=set_null_dict(get_or_none(mongo_obj, "notification")),
        )
        session.add(schedule)

    def has_migrate_phase_2(self) -> bool:
        return True

    def _add_duration(
        self, session: so.Session, schedule_id: UUID, default: bool, mongo_duration
    ) -> None:
        duration = dbm.ScheduleDuration(
            default=default,
            mongo_val=mongo_duration,
            value=mongo_duration["value"],
            on=mongo_duration["on"],
        )
        duration.schedule_id = schedule_id
        if "worker" in mongo_duration and mongo_duration["worker"]:
            worker_id = None
            try:
                worker_id = self._cache.get_pg_worker_id_by_workername(
                    session,
                    mongo_duration["worker"],
                    used_by_str="not used",
                )
            except KeyNotFoundException:
                pass
            if worker_id:
                duration.worker_id = worker_id
            else:
                if not default:
                    # do not insert duration of workers which are not knowm anymore
                    return

        if "task" in mongo_duration and mongo_duration["task"]:
            # we do not use a cache since we do not expect to use the same task twice
            task_id = session.execute(
                sa.select(dbm.Task.id).where(
                    dbm.Task.mongo_id == str(mongo_duration["task"])
                )
            ).scalar_one_or_none()
            if task_id:
                duration.task_id = task_id
            # nota: we don't mind if the task_id is not set, it is not a mandatory
            # information
        session.add(duration)

    def migrate_one_doc_phase_2(self, session: so.Session, mongo_obj) -> None:
        # we do not use a cache since we do not expect to use the same schedule twice
        schedule = session.execute(
            sa.select(dbm.Schedule).where(
                dbm.Schedule.mongo_id == str(mongo_obj["_id"])
            )
        ).scalar_one()
        if "most_recent_task" in mongo_obj and "_id" in mongo_obj["most_recent_task"]:
            task_mongo_id = str(mongo_obj["most_recent_task"]["_id"])
            # we do not use a cache since we do not expect to use the same task twice
            # + it is possible that the most recent task is now missing
            schedule.most_recent_task_id = session.execute(
                sa.select(dbm.Task.id).where(dbm.Task.mongo_id == task_mongo_id)
            ).scalar_one_or_none()
        if "duration" in mongo_obj:
            if "default" in mongo_obj["duration"]:
                self._add_duration(
                    default=True,
                    session=session,
                    schedule_id=schedule.id,
                    mongo_duration=mongo_obj["duration"]["default"],
                )
            if "workers" in mongo_obj["duration"]:
                for _, worker_obj in mongo_obj["duration"]["workers"].items():
                    self._add_duration(
                        default=False,
                        session=session,
                        schedule_id=schedule.id,
                        mongo_duration=worker_obj,
                    )


class RequestedTaskMigrator(Migrator):
    cache: Dict[str, str] = {}

    def get_mongo_object_name(self) -> str:
        return "requestedtask"

    def get_mongo_collection(self) -> BaseCollection:
        return mongo.RequestedTasks()

    def get_sql_tables(self) -> List[Tuple[str, dbm.Base]]:
        return [("requestedtask", dbm.RequestedTask)]

    def get_expected_mongo_keys(self) -> List[str]:
        return [
            "_id",
            "schedule_name",
            "status",
            "requested_by",
            "priority",
            "worker",
        ]

    def get_expected_mongo_json_objects(self) -> List[str]:
        return ["events", "config", "upload", "timestamp", "notification"]

    def migrate_one_doc_phase_1(self, session: so.Session, mongo_obj) -> None:
        schedule_id = self._cache.get_pg_schedule_id_by_schedulename(
            session=session,
            schedulename=mongo_obj["schedule_name"],
            used_by_str=(
                f"property 'schedule_name' in requested task {str(mongo_obj['_id'])}"
            ),
        )
        if mongo_obj["worker"]:
            worker_id = self._cache.get_pg_worker_id_by_workername(
                session=session,
                workername=mongo_obj["worker"],
                used_by_str=(
                    f"property 'worker' in requested task {str(mongo_obj['_id'])}"
                ),
            )
        else:
            worker_id = None

        updated_at = get_updated_at(mongo_obj)
        raise_if_none(
            updated_at,
            Exception,
            "impossible to compute 'updated_at' for requested task",
        )
        task = dbm.RequestedTask(
            mongo_val=mongo_obj,
            mongo_id=str(mongo_obj["_id"]),
            status=mongo_obj["status"],
            timestamp=mongo_obj["timestamp"],
            events=mongo_obj["events"],
            requested_by=mongo_obj["requested_by"],
            priority=mongo_obj["priority"],
            config=mongo_obj["config"],
            upload=mongo_obj["upload"],
            notification=set_null_dict(get_or_none(mongo_obj, "notification")),
            updated_at=updated_at,
        )
        task.schedule_id = schedule_id
        task.worker_id = worker_id
        session.add(task)

    def has_migrate_phase_2(self) -> bool:
        return False

    def migrate_one_doc_phase_2(self, session: so.Session, mongo_obj) -> None:
        pass


def get_updated_at(data) -> str:
    updated_at = None
    for event in data.get("events", []):
        if updated_at is None:
            updated_at = event["timestamp"]
        else:
            updated_at = max(updated_at, event["timestamp"])
    return updated_at


class TaskMigrator(Migrator):
    cache: Dict[str, str] = {}

    def get_mongo_object_name(self) -> str:
        return "task"

    def get_mongo_collection(self) -> BaseCollection:
        return mongo.Tasks()

    def get_sql_tables(self) -> List[Tuple[str, dbm.Base]]:
        return [("task", dbm.Task)]

    def get_expected_mongo_keys(self) -> List[str]:
        return [
            "_id",
            "status",
            "schedule_name",
            "schedule_id",
            "worker",
            "priority",
            "requested_by",
            "canceled_by",
        ]

    def get_expected_mongo_json_objects(self) -> List[str]:
        return [
            "events",
            "debug",
            "container",
            "config",
            "notification",
            "files",
            "timestamp",
            "upload",
        ]

    def migrate_one_doc_phase_1(self, session: so.Session, mongo_obj) -> None:
        try:
            schedule_id = self._cache.get_pg_schedule_id_by_schedulename(
                session=session,
                schedulename=mongo_obj["schedule_name"],
                used_by_str=(
                    "property 'schedule_name' in requested task"
                    f" {str(mongo_obj['_id'])}"
                ),
            )
        except KeyNotFoundException:
            schedule_id = None
        if schedule_id is None:
            # do not migrate tasks which are associated with a schedule which does not
            # exists anymore
            return
        try:
            worker_id = self._cache.get_pg_worker_id_by_workername(
                session=session,
                workername=mongo_obj["worker"],
                used_by_str=(
                    f"property 'worker' in requested task {str(mongo_obj['_id'])}"
                ),
            )
        except KeyNotFoundException:
            worker_id = None
        if worker_id is None:
            # do not migrate tasks which are associated with a worker which does not
            # exists anymore
            return
        updated_at = get_updated_at(mongo_obj)
        if updated_at is None:
            # do not migrate tasks which have no updated_at, i.e no event, it makes no
            # sense
            return
        task = dbm.Task(
            mongo_val=mongo_obj,
            mongo_id=str(mongo_obj["_id"]),
            events=mongo_obj["events"],
            debug=set_null_dict(get_or_none(mongo_obj, "debug")),
            status=mongo_obj["status"],
            requested_by=get_or_none(mongo_obj, "requested_by"),
            canceled_by=get_or_none(mongo_obj, "canceled_by"),
            timestamp=mongo_obj["timestamp"],
            container=set_null_dict(
                self.cleanup_stdout(get_or_none(mongo_obj, "container"))
            ),
            priority=mongo_obj["priority"],
            config=mongo_obj["config"],
            notification=set_null_dict(get_or_none(mongo_obj, "notification")),
            files=set_null_dict(
                self.cleanup_check_logs(get_or_none(mongo_obj, "files"))
            ),
            upload=set_null_dict(get_or_none(mongo_obj, "upload")),
            updated_at=get_updated_at(mongo_obj),
        )
        task.schedule_id = schedule_id
        task.worker_id = worker_id
        session.add(task)

    def cleanup_check_logs(self, files):
        """Escape null unicode character \u0000 which is not allowed by PG"""
        if files is None:
            return None
        for _, aFile in files.items():
            if "check_log" in aFile and aFile["check_log"]:
                aFile["check_log"] = aFile["check_log"].replace("\u0000", "\\u0000")
        return files

    def cleanup_stdout(self, container):
        """Escape null unicode character \u0000 which is not allowed by PG"""
        if container is None:
            return None
        if "stdout" in container and container["stdout"]:
            container["stdout"] = container["stdout"].replace("\u0000", "\\u0000")
        return container

    def has_migrate_phase_2(self) -> bool:
        return False

    def migrate_one_doc_phase_2(self, session: so.Session, mongo_obj) -> None:
        pass


def main():
    logger.info("Migrating data from Mongo to PostgreSQL")

    Initializer.check_if_schema_is_up_to_date()

    # init a cache of mongo property to pg ID to avoid fetching them too many
    # times from DB
    cache = MigrationCache()

    # this is the list of migrator to run ; order is important since we assume
    # in the migrator that some other object are already present. For instance,
    # when migrating the refresh tokens we assume that users are already present
    # in DB and we can fetch their ID
    migrators: List[Migrator] = [
        UserMigrator(cache),
        RefreshTokenMigrator(cache),
        WorkerMigrator(cache),
        ScheduleMigrator(cache),
        RequestedTaskMigrator(cache),
        TaskMigrator(
            cache, 10
        ),  # commit every 10 documents for tasks because some of them are VERY big
    ]

    # first check that all tables are empty, migration is not re-entrant
    if not tables_are_empty(migrators):
        logger.error("Please fix warnings before proceeding with the migration")
        return

    # run phase 1 (i.e. bulk load)
    for migrator in migrators:
        migrator.migrate_phase_1()

    # run phase 2 (create properties / objects with dependencies)
    for migrator in migrators:
        if migrator.has_migrate_phase_2():
            migrator.migrate_phase_2()


if __name__ == "__main__":
    main()
