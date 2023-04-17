import datetime

import pytest
import sqlalchemy as sa
from werkzeug.security import generate_password_hash

import db.models as dbm
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
def make_schedule(make_language, make_config):
    schedule_ids = []

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
            schedule_id = schedule.id
            schedule_ids.append(schedule_id)
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

    with Session.begin() as session:
        for schedule in session.execute(
            sa.select(dbm.Schedule).where(dbm.Schedule.id.in_(schedule_ids))
        ).scalars():
            session.delete(schedule)


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
def make_user(database):
    user_ids = []

    def _make_user(username: str = "some-user", role: str = None) -> dict:
        user = dbm.User(
            mongo_val=None,
            mongo_id=None,
            username=username,
            password_hash=generate_password_hash("some-password"),
            # (
            #     "pbkdf2:sha256:150000$dEqsZI8W$2d2bbcbadab59281528ecbb27d26ac628472a0b"
            #     "2f0a5e1828edbeeae683dd40f"
            # ),
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
            user_id = user.id
            user_ids.append(user_id)
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

    with Session.begin() as session:
        for user in session.execute(
            sa.select(dbm.User).where(dbm.User.id.in_(user_ids))
        ).scalars():
            session.delete(user)
