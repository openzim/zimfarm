import pytest
from bson import ObjectId


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
        }

    return _make_config


@pytest.fixture(scope="module")
def make_schedule(database, make_language, make_config):
    schedule_ids = []

    def _make_schedule(
        name: str = "schedule_name",
        category: str = "wikipedia",
        tags: list = ["nopic"],
        language: dict = None,
        config: dict = None,
    ) -> dict:
        document = {
            "_id": ObjectId(),
            "name": name,
            "category": category,
            "enabled": True,
            "language": language or make_language(),
            "tags": tags,
            "config": config or make_config(),
        }
        schedule_id = database.schedules.insert_one(document).inserted_id
        schedule_ids.append(schedule_id)
        return document

    yield _make_schedule

    database.schedules.delete_many({"_id": {"$in": schedule_ids}})


@pytest.fixture(scope="module")
def schedule(make_schedule):
    return make_schedule()


@pytest.fixture(scope="module")
def schedules(make_schedule, make_config, make_language):
    schedules = []
    for index in range(38):
        name = "schedule_{}".format(index)
        schedule = make_schedule(name)
        schedules.append(schedule)

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
