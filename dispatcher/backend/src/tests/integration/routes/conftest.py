import datetime

import pytest
from werkzeug.security import generate_password_hash

import db.models as dbm
from common import getnow
from common.enum import TaskStatus
from common.roles import ROLES
from db import Session


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
            mongo_val=None,
            mongo_id=None,
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
def make_user(garbage_collector):
    def _make_user(username: str = "some-user", role: str = None) -> dict:
        user = dbm.User(
            mongo_val=None,
            mongo_id=None,
            username=username,
            password_hash=generate_password_hash("some-password"),
            scope=None,
            email=f"{username}@acme.com",
        )
        user.ssh_keys.append(
            dbm.Sshkey(
                mongo_val=None,
                name="pytest",
                fingerprint="a4a7cfd26a11ec519b63d4d12f34ecf2",
                key=(
                    "AAAAB3NzaC1yc2EAAAADAQABAAABAQC4EYmNPfdscaYcMTXe0NxSpS+5qbVO+"
                    "WDaMLt/JLbDmorJzzBYFItxsr5hvxKckQ3jgUdcoIqzpwfjg88NhxenPmLlqs"
                    "aQfkI2IjmOxDwaH4zs1IKG4+BTyY6EFrEnWgO9vJMJPOVzBdv3uUUOULvTnE7"
                    "ZWpqb+2tRQCk6GUF9AoajmAzTlu+PjD53kRqwRugK/EKrqIjg5Nb/y5F4xGXL"
                    "Tb3otsUp+iFB3TJ65yB9F4C/Q4R5Srr/R3CWBQvoMLHUjya7HppoEW5sl8e+n"
                    "EYpwKVCVuyJiRv9NuomBuh2ZH7ftfY8zxkVyv6UbVNXwFTvT3QVbwM6pQgVx/"
                    "nJmzeb"
                ),
                type="RSA",
                added=datetime.datetime(2019, 1, 1),
                last_used=datetime.datetime(2019, 1, 1),
                pkcs8_key="-----BEGIN PUBLIC KEY-----\n"
                "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAuBGJjT33bHGmHDE13tDc\n"
                "UqUvuam1Tvlg2jC7fyS2w5qKyc8wWBSLcbK+Yb8SnJEN44FHXKCKs6cH44PPDYcX\n"
                "pz5i5arGkH5CNiI5jsQ8Gh+M7NSChuPgU8mOhBaxJ1oDvbyTCTzlcwXb97lFDlC7\n"
                "05xO2Vqam/trUUApOhlBfQKGo5gM05bvj4w+d5EasEboCvxCq6iI4OTW/8uReMRl\n"
                "y0296LbFKfohQd0yeucgfReAv0OEeUq6/0dwlgUL6DCx1I8mux6aaBFubJfHvpxG\n"
                "KcClQlbsiYkb/TbqJgbodmR+37X2PM8ZFcr+lG1TV8BU7090FW8DOqUIFcf5yZs3\n"
                "mwIDAQAB\n"
                "-----END PUBLIC KEY-----\n",
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
            schedule = dbm.Schedule.get_or_none(session, schedule_name)
            if schedule is None:
                make_schedule(schedule_name)
                schedule = dbm.Schedule.get_or_none(session, schedule_name)
            requested_task = dbm.RequestedTask(
                mongo_val=None,
                mongo_id=None,
                status=status,
                timestamp=timestamp,
                updated_at=now,
                events=events,
                requested_by=requested_by,
                priority=priority,
                config=config,
                upload={},
                notification={},
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
    ) -> dict:
        with Session.begin() as session:
            user_id = dbm.User.get_id_or_none(session, username)
            worker = dbm.Worker(
                mongo_val=None,
                mongo_id=None,
                name=name,
                selfish=False,
                cpu=3,
                memory=1024,
                disk=1024,
                offliners=["mwoffliner", "youtube"],
                platforms={},
                last_seen=last_seen,
                last_ip=last_ip,
            )
            worker.user_id = user_id
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
def workers(make_worker, make_user, make_config, make_language):
    for index in range(2):
        make_user(f"user_{index}")
    workers = []
    for index in range(38):
        name = f"worker_{index}"
        username = (
            f"user_{index%2}"  # build some users as well but not as many as workers
        )
        last_ip = f"192.168.1.{index}"
        worker = make_worker(name, username=username, last_ip=last_ip)
        workers.append(worker)
    return workers
