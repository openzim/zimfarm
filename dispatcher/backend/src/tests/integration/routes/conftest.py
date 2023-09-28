import datetime

import pytest
from werkzeug.security import generate_password_hash

import db.models as dbm
from common import getnow
from common.enum import TaskStatus
from common.roles import ROLES
from db import Session
from utils.offliners import expanded_config


@pytest.fixture(scope="module")
def make_language():
    def _make_language(
        code: str = "en",
        name_en: str = "language_en",
        name_native: str = "language_native",
    ) -> dict:
        return {"code": code, "name_en": name_en, "name_native": name_native}

    return _make_language


@pytest.fixture(scope="module")
def make_config():
    def _make_config(sub_domain: str = "en", fmt: str = "nopic") -> dict:
        return {
            "task_name": "mwoffliner",
            "image": {"name": "openzim/mwoffliner", "tag": "latest"},
            "flags": {
                "mwUrl": "https://{}.wikipedia.org".format(sub_domain),
                "adminEmail": "test@kiwix.org",
                "format": fmt,
                "withZimFullTextIndex": True,
            },
            "warehouse_path": "/wikipedia",
            "resources": {"cpu": 1, "memory": 2**30, "disk": 2**30},
        }

    return _make_config


@pytest.fixture(scope="module")
def make_schedule(make_language, make_config, garbage_collector):
    def _make_schedule(
        name: str = "schedule_name",
        category: str = "wikipedia",
        tags: list = ["nopic"],
        language: dict = None,
        config: dict = None,
        periodicity: str = "monthly",
    ) -> dict:
        if not language:
            language = make_language()
        schedule = dbm.Schedule(
            name=name,
            category=category,
            enabled=True,
            language_code=language["code"],
            language_name_en=language["name_en"],
            language_name_native=language["name_native"],
            tags=tags,
            config=config or make_config(),
            periodicity=periodicity,
            notification=None,
        )
        with Session.begin() as session:
            session.add(schedule)
            session.flush()
            garbage_collector.add_schedule_id(schedule.id)
            document = {
                "_id": schedule.id,
                "name": schedule.name,
                "category": schedule.category,
                "enabled": schedule.enabled,
                "language": {
                    "code": schedule.language_code,
                    "name_en": schedule.language_name_en,
                    "name_native": schedule.language_name_native,
                },
                "tags": schedule.tags,
                "config": schedule.config,
                "periodicity": schedule.periodicity,
                "notification": schedule.notification,
            }
        return document

    yield _make_schedule


@pytest.fixture(scope="module")
def schedule(make_schedule):
    return make_schedule()


@pytest.fixture(scope="module")
def schedules(make_schedule, make_config, make_language):
    schedules = []
    for index in range(38):
        schedules.append(make_schedule(name="schedule_{}".format(index)))

    # custom schedules for query lookup
    schedules.append(make_schedule(name="wikipedia_fr_all_maxi"))
    schedules.append(make_schedule(name="wikipedia_fr_all_nopic"))
    schedules.append(make_schedule(name="wikipedia_bm_all_nopic"))
    schedules.append(make_schedule(name="schedule_42", category="gutenberg"))
    schedules.append(
        make_schedule(language=make_language(code="fr"), name="schedule_43")
    )
    schedules.append(
        make_schedule(language=make_language(code="bm"), name="schedule_44")
    )
    schedules.append(make_schedule(category="phet", name="schedule_45"))
    schedules.append(make_schedule(category="wikibooks", name="schedule_46"))
    schedules.append(make_schedule(tags=["all"], name="schedule_47"))
    schedules.append(make_schedule(tags=["all", "mini"], name="schedule_48"))
    schedules.append(make_schedule(tags=["mini", "nopic"], name="schedule_49"))
    schedules.append(make_schedule(config=make_config()))
    schedules.append(
        make_schedule(
            config=make_config(),
            name="youtube_fr_all_novid",
            language=make_language(code="fr"),
            category="other",
            tags=["nopic", "novid"],
        )
    )
    return schedules


@pytest.fixture(scope="module")
def make_key():
    def _make_key() -> dict:
        return {
            "name": "pytest",
            "fingerprint": "a4a7cfd26a11ec519b63d4d12f34ecf2",
            "key": (
                "AAAAB3NzaC1yc2EAAAADAQABAAABAQC4EYmNPfdscaYcMTXe0NxSpS+5qbVO+"
                "WDaMLt/JLbDmorJzzBYFItxsr5hvxKckQ3jgUdcoIqzpwfjg88NhxenPmLlqs"
                "aQfkI2IjmOxDwaH4zs1IKG4+BTyY6EFrEnWgO9vJMJPOVzBdv3uUUOULvTnE7"
                "ZWpqb+2tRQCk6GUF9AoajmAzTlu+PjD53kRqwRugK/EKrqIjg5Nb/y5F4xGXL"
                "Tb3otsUp+iFB3TJ65yB9F4C/Q4R5Srr/R3CWBQvoMLHUjya7HppoEW5sl8e+n"
                "EYpwKVCVuyJiRv9NuomBuh2ZH7ftfY8zxkVyv6UbVNXwFTvT3QVbwM6pQgVx/"
                "nJmzeb"
            ),
            "type": "RSA",
            "added": datetime.datetime(2019, 1, 1),
            "last_used": datetime.datetime(2019, 1, 1),
            "pkcs8_key": "-----BEGIN PUBLIC KEY-----\n"
            "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAuBGJjT33bHGmHDE13tDc\n"
            "UqUvuam1Tvlg2jC7fyS2w5qKyc8wWBSLcbK+Yb8SnJEN44FHXKCKs6cH44PPDYcX\n"
            "pz5i5arGkH5CNiI5jsQ8Gh+M7NSChuPgU8mOhBaxJ1oDvbyTCTzlcwXb97lFDlC7\n"
            "05xO2Vqam/trUUApOhlBfQKGo5gM05bvj4w+d5EasEboCvxCq6iI4OTW/8uReMRl\n"
            "y0296LbFKfohQd0yeucgfReAv0OEeUq6/0dwlgUL6DCx1I8mux6aaBFubJfHvpxG\n"
            "KcClQlbsiYkb/TbqJgbodmR+37X2PM8ZFcr+lG1TV8BU7090FW8DOqUIFcf5yZs3\n"
            "mwIDAQAB\n"
            "-----END PUBLIC KEY-----\n",
        }

    yield _make_key


@pytest.fixture(scope="module")
def key(make_key):
    return make_key()


@pytest.fixture(scope="module")
def make_user(garbage_collector, key):
    def _make_user(
        username: str = "some-user", role: str = None, deleted: bool = False
    ) -> dict:
        user = dbm.User(
            username=username,
            password_hash=generate_password_hash("some-password"),
            scope=None,
            email=f"{username}@acme.com",
            deleted=deleted,
        )
        user.ssh_keys.append(
            dbm.Sshkey(
                name=key["name"],
                fingerprint=key["fingerprint"],
                key=key["key"],
                type=key["type"],
                added=key["added"],
                last_used=key["last_used"],
                pkcs8_key=key["pkcs8_key"],
            )
        )
        if role:
            user.scope = ROLES.get(role)
        with Session.begin() as session:
            session.add(user)
            session.flush()
            garbage_collector.add_user_id(user.id)
            res_obj = {
                "username": user.username,
                "password_hash": user.password_hash,
                "scope": user.scope,
                "email": user.email,
                "ssh_keys": [
                    {
                        "name": key.name,
                        "fingerprint": key.fingerprint,
                        "key": key.key,
                        "type": key.type,
                        "added": key.added,
                        "last_used": key.last_used,
                        "pkcs8_key": key.pkcs8_key,
                    }
                    for key in user.ssh_keys
                ],
            }
        return res_obj

    yield _make_user


@pytest.fixture(scope="module")
def user(make_user):
    return make_user()


@pytest.fixture(scope="module")
def deleted_user(make_user):
    return make_user(username="del_some-user", deleted=True)


@pytest.fixture(scope="module")
def make_event():
    def _make_event(code: str, timestamp: datetime, **kwargs):
        event = {"code": code, "timestamp": timestamp}
        event.update(kwargs)
        return event

    return _make_event


@pytest.fixture(scope="module")
def make_requested_task(make_event, make_schedule, garbage_collector):
    # requested_task_ids = []

    def _make_requested_task(
        schedule_name="",
        status=TaskStatus.requested,
        requested_by="someone",
        priority=0,
    ):
        events = [TaskStatus.requested]
        now = getnow()
        timestamp = {event: now for event in events}
        events = [make_event(event, timestamp[event]) for event in events]

        config = {
            "flags": {"api-key": "aaaaaa", "id": "abcde", "type": "channel"},
            "image": {"name": "openzim/youtube", "tag": "latest"},
            "task_name": "youtube",
            "warehouse_path": "/other",
            "resources": {"cpu": 3, "memory": 1024, "disk": 1024},
        }

        with Session.begin() as session:
            schedule = dbm.Schedule.get(session, schedule_name, run_checks=False)
            if schedule is None:
                make_schedule(schedule_name)
                schedule = dbm.Schedule.get(session, schedule_name)
            requested_task = dbm.RequestedTask(
                status=status,
                timestamp=timestamp,
                updated_at=now,
                events=events,
                requested_by=requested_by,
                priority=priority,
                config=config,
                upload={},
                notification={},
                original_schedule_name=schedule_name,
            )
            requested_task.schedule = schedule
            session.add(requested_task)
            session.flush()
            garbage_collector.add_requested_task_id(requested_task.id)

            return {
                "_id": requested_task.id,
                "status": requested_task.status,
                "schedule_name": requested_task.schedule.name,
                "timestamp": requested_task.timestamp,
                "events": requested_task.events,
                "config": requested_task.config,
                "notification": requested_task.notification,
                "priority": requested_task.priority,
                "requested_by": requested_task.requested_by,
                "upload": requested_task.upload,
                "updated_at": requested_task.updated_at,
            }

    yield _make_requested_task


@pytest.fixture(scope="module")
def requested_tasks(make_requested_task):
    tasks = []
    for i in range(5):
        tasks += [
            make_requested_task(status=TaskStatus.requested),
            make_requested_task(status=TaskStatus.reserved),
            make_requested_task(status=TaskStatus.started),
            make_requested_task(status=TaskStatus.succeeded),
            make_requested_task(status=TaskStatus.failed),
        ]
    return tasks


@pytest.fixture(scope="module")
def requested_task(make_requested_task):
    return make_requested_task()


@pytest.fixture(scope="module")
def make_worker(user, garbage_collector):
    def _make_worker(
        name: str = "worker_name",
        username: str = "some-user",
        last_seen: datetime = getnow(),
        resources: dict = None,
        last_ip: str = "192.168.1.1",
        deleted: bool = False,
    ) -> dict:
        with Session.begin() as session:
            user = dbm.User.get(session, username, run_checks=False)
            worker = dbm.Worker(
                name=name,
                selfish=False,
                cpu=3,
                memory=1024,
                disk=1024,
                offliners=["mwoffliner", "youtube"],
                platforms={},
                last_seen=last_seen,
                last_ip=last_ip,
                deleted=deleted,
            )
            worker.user_id = user.id
            session.add(worker)
            session.flush()
            garbage_collector.add_worker_id(worker.id)
            document = {
                "name": worker.name,
                "username": worker.user.username,
                "offliners": worker.offliners,
                "last_seen": worker.last_seen,
                "last_ip": worker.last_ip,
                "resources": {
                    "cpu": worker.cpu,
                    "disk": worker.disk,
                    "memory": worker.memory,
                },
            }
        return document

    yield _make_worker


@pytest.fixture(scope="module")
def worker(make_worker):
    return make_worker()


@pytest.fixture(scope="module")
def workers(make_worker, make_user, make_config, make_language, deleted_user):
    for index in range(2):
        make_user(f"user_{index}")
    workers = []
    for index in range(38):
        name = f"worker_{index}"
        username = (
            f"user_{index%2}"  # build some users as well but not as many as workers
        )
        last_ip = (
            (
                # tweak one IP to have duplicates
                f"192.168.1.{index if index != 2 else 1}"
            )
            # tweak one IP to be missing (worker without any last_ip for now)
            if index != 3
            else None
        )
        worker = make_worker(name, username=username, last_ip=last_ip)
        workers.append(worker)

    # add one deleted worker
    name = "deleted_worker"
    worker = make_worker(name=name, deleted=True, last_ip="192.168.1.254")
    workers.append(worker)

    # add one worker on a deleted user
    name = "worker_from_deleted_user"
    worker = make_worker(
        name=name, username=deleted_user["username"], last_ip="192.168.1.253"
    )
    workers.append(worker)

    return workers


@pytest.fixture(scope="module")
def make_task(make_event, make_schedule, make_config, worker, garbage_collector):
    def _make_task(
        schedule_name="schedule_name",
        status=TaskStatus.succeeded,
    ):
        now = getnow()
        if status == TaskStatus.requested:
            events = [TaskStatus.requested]
        elif status == TaskStatus.reserved:
            events = [TaskStatus.requested, TaskStatus.reserved]
        elif status == TaskStatus.started:
            events = [TaskStatus.requested, TaskStatus.reserved, TaskStatus.started]
        elif status == TaskStatus.succeeded:
            events = [
                TaskStatus.requested,
                TaskStatus.reserved,
                TaskStatus.started,
                TaskStatus.succeeded,
            ]
        else:
            events = [
                TaskStatus.requested,
                TaskStatus.reserved,
                TaskStatus.started,
                TaskStatus.failed,
            ]

        timestamp = {event: now for event in events}
        events = [make_event(event, timestamp[event]) for event in events]
        container = {
            "command": "mwoffliner --mwUrl=https://example.com",
            "image": {"name": "mwoffliner", "tag": "1.8.0"},
            "exit_code": 0,
            "stderr": "example_stderr",
            "stdout": "example_stdout",
        }
        debug = {"args": [], "kwargs": {}}

        if status == TaskStatus.failed:
            debug["exception"] = "example_exception"
            debug["traceback"] = "example_traceback"
            files = {}
        else:
            files = {"mwoffliner_1.zim": {"name": "mwoffliner_1.zim", "size": 1000}}
        config = expanded_config(make_config())
        with Session.begin() as session:
            worker_obj = dbm.Worker.get(session, worker["name"])
            schedule = dbm.Schedule.get(session, schedule_name, run_checks=False)
            if schedule is None:
                make_schedule(schedule_name)
                schedule = dbm.Schedule.get(session, schedule_name)
            task = dbm.Task(
                updated_at=now,
                events=events,
                debug=debug,
                status=status,
                timestamp=timestamp,
                requested_by="bob",
                canceled_by=None,
                container=container,
                priority=1,
                config=config,
                notification={},
                files=files,
                upload={},
                original_schedule_name=schedule_name,
            )
            task.schedule_id = schedule.id
            task.worker_id = worker_obj.id
            session.add(task)
            session.flush()
            garbage_collector.add_task_id(task.id)

            return {
                "_id": task.id,
                "status": task.status,
                "worker": worker_obj.name,
                "schedule_name": schedule.name,
                "timestamp": task.timestamp,
                "events": task.events,
                "container": task.container,
                "debug": task.debug,
                "files": task.files,
            }

    yield _make_task


@pytest.fixture(scope="module")
def tasks(make_task):
    tasks = []
    for i in range(5):
        tasks += [
            make_task(status=TaskStatus.requested),
            make_task(status=TaskStatus.reserved),
            make_task(status=TaskStatus.started),
            make_task(status=TaskStatus.succeeded),
            make_task(status=TaskStatus.failed),
        ]
    return tasks


@pytest.fixture(scope="module")
def task(make_task):
    return make_task(status=TaskStatus.succeeded)
