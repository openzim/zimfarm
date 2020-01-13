from uuid import uuid4

from bson import ObjectId
import pytest

from utils.offliners import command_information_for

ONE_GiB = 2 ** 30
ONE_MiB = 1048576
MIN_RAM = 512 * ONE_MiB


@pytest.fixture()
def schedule(make_schedule):
    return make_schedule(name=str(uuid4()))


good_patch_updates = [
    {"language": {"code": "bm", "name_en": "Bambara", "name_native": "Bamanankan"}},
    {"enabled": False},
    {"enabled": True},
    {"category": "psiram"},
    {"tags": []},
    {"tags": ["full"]},
    {"tags": ["full", "small"]},
    {"tags": ["full", "small"], "category": "vikidia", "enabled": False},
    {"task_name": "phet", "flags": {}},
    {"flags": {"mwUrl": "https://fr.wikipedia.org", "adminEmail": "hello@test.de"}},
    {"warehouse_path": "/phet"},
    {"image": {"name": "openzim/phet", "tag": "latest"}},
    {"resources": {"cpu": 3, "memory": MIN_RAM, "disk": ONE_GiB}},
    {
        "task_name": "gutenberg",
        "warehouse_path": "/gutenberg",
        "flags": {},
        "image": {"name": "openzim/gutenberg", "tag": "latest"},
        "resources": {"cpu": 3, "memory": MIN_RAM, "disk": ONE_GiB},
    },
    {"name": "new_name"},
]

bad_patch_updates = [
    {},
    {"language": {"name_en": "Bambara", "name_native": "Bamanankan"}},
    {"language": {"code": "bm", "name_en": "", "name_native": "Bamanankan"}},
    {"language": {"code": "bm", "name_en": "Bambara"}},
    {"enabled": "False"},
    {"category": "ubuntu"},
    {"tags": ""},
    {"tags": ["full", 1]},
    {"tags": "full,small"},
    {"name": ""},
    {"config": ""},
    {"flags": {}},
    {
        "task_name": "hop",
        "warehouse_path": "/phet",
        "flags": {},
        "image": {"name": "openzim/phet", "tag": "latest"},
        "resources": {"cpu": 3, "memory": MIN_RAM, "disk": ONE_GiB},
    },
    {
        "task_name": "phet",
        "warehouse_path": "/ubuntu",
        "flags": {},
        "image": {"name": "openzim/phet", "tag": "latest"},
        "resources": {"cpu": 3, "memory": MIN_RAM, "disk": ONE_GiB},
    },
    {
        "task_name": "phet",
        "warehouse_path": "/phet",
        "flags": {"mwUrl": "http://fr.wikipedia.org"},
        "image": {"name": "openzim/phet", "tag": "latest"},
        "resources": {"cpu": 3, "memory": MIN_RAM, "disk": ONE_GiB},
    },
    {
        "task_name": "phet",
        "warehouse_path": "/phet",
        "flags": {},
        "image": {"name": "openzim/youtuba", "tag": "latest"},
        "resources": {"cpu": 3, "memory": MIN_RAM, "disk": ONE_GiB},
    },
    {
        "task_name": "gutenberg",
        "warehouse_path": "/gutenberg",
        "flags": {},
        "image": {"name": "openzim/youtube", "tag": "latest"},
        "resources": {"cpu": -1, "memory": MIN_RAM, "disk": ONE_GiB},
    },
]


class TestScheduleList:
    def test_list_schedules_no_param(self, client, schedules):

        url = "/schedules/"
        response = client.get(url)
        assert response.status_code == 200

        response_json = response.get_json()
        assert "items" in response_json
        assert len(response_json["items"]) == 20
        for item in response_json["items"]:
            assert isinstance(item["category"], str)
            assert isinstance(item["name"], str)
            assert isinstance(item["language"]["code"], str)
            assert isinstance(item["language"]["name_en"], str)
            assert isinstance(item["language"]["name_native"], str)

    @pytest.mark.parametrize(
        "skip, limit, expected",
        [(0, 30, 30), (10, 15, 15), (40, 25, 11), (100, 100, 0)],
    )
    def test_list_schedules_with_param(self, client, schedules, skip, limit, expected):

        url = "/schedules/?skip={}&limit={}".format(skip, limit)
        response = client.get(url)
        assert response.status_code == 200

        response_json = response.get_json()
        assert "items" in response_json
        assert len(response_json["items"]) == expected

    @pytest.mark.parametrize(
        "params, expected",
        [
            ("name=Wikipedia_fr", 2),
            ("name=Wikipedia", 3),
            ("name=Wiki.*pic$", 2),
            ("lang=fr", 2),
            ("lang=bm", 1),
            ("lang=bm&lang=fr", 3),
            ("category=phet", 1),
            ("category=gutenberg", 1),
            ("category=wikibooks", 1),
            ("category=wikipedia", 47),
            ("category=phet&category=wikipedia", 48),
            ("category=gutenberg&category=phet&category=wikipedia", 49),
            ("tag=all", 2),
            ("tag=mini", 2),
            ("tag=all&tag=mini", 1),
            ("name=youtube&lang=fr&category=other&tag=nopic&tag=novid", 1),
        ],
    )
    def test_list_schedules_with_filter(self, client, schedules, params, expected):

        url = "/schedules/?{}&limit=50".format(params)
        response = client.get(url)
        assert response.status_code == 200

        response_json = response.get_json()
        assert "items" in response_json
        assert len(response_json["items"]) == expected


class TestSchedulePost:
    @pytest.mark.parametrize(
        "document",
        [
            {
                "name": "wikipedia_bm_test",
                "category": "wikipedia",
                "enabled": False,
                "tags": ["full"],
                "language": {
                    "code": "bm",
                    "name_en": "Bambara",
                    "name_native": "Bamanankan",
                },
                "periodicity": "monthly",
                "config": {
                    "task_name": "phet",
                    "warehouse_path": "/phet",
                    "flags": {},
                    "image": {"name": "openzim/phet", "tag": "latest"},
                    "resources": {"cpu": 3, "memory": MIN_RAM, "disk": ONE_GiB},
                },
            },
            {
                "name": "gutenberg_mul",
                "category": "gutenberg",
                "enabled": True,
                "tags": ["full", "mul"],
                "language": {
                    "code": "mul",
                    "name_en": "Multiple Languages",
                    "name_native": "Multiple Languages",
                },
                "periodicity": "annually",
                "config": {
                    "task_name": "gutenberg",
                    "warehouse_path": "/gutenberg",
                    "flags": {},
                    "image": {"name": "openzim/gutenberg", "tag": "latest"},
                    "resources": {"cpu": 3, "memory": MIN_RAM, "disk": ONE_GiB},
                },
            },
        ],
    )
    def test_create_schedule(self, database, client, access_token, document):
        url = "/schedules/"
        response = client.post(
            url, json=document, headers={"Authorization": access_token}
        )
        print(response.get_json())
        assert response.status_code == 201
        schedule_id = response.get_json()["_id"]

        url = "/schedules/{}".format(document["name"])
        response = client.get(url, headers={"Authorization": access_token})
        assert response.status_code == 200

        response_json = response.get_json()
        document["config"].update(command_information_for(document["config"]))
        response_json.pop("duration", None)  # generated server-side
        assert response_json == document

        # remove from DB to prevent count mismatch on other tests
        database.schedules.delete_one({"_id": ObjectId(schedule_id)})

    @pytest.mark.parametrize(
        "key", ["name", "category", "enabled", "tags", "language", "config"]
    )
    def test_create_schedule_missing_keys(self, client, access_token, key):
        schedule = {
            "name": "wikipedia_bm_test",
            "category": "wikipedia",
            "enabled": False,
            "tags": ["full"],
            "language": {
                "code": "bm",
                "name_en": "Bambara",
                "name_native": "Bamanankan",
            },
            "config": {
                "task_name": "phet",
                "warehouse_path": "/phet",
                "flags": {},
                "image": {"name": "openzim/phet", "tag": "latest"},
            },
        }

        del schedule[key]
        url = "/schedules/"
        response = client.post(
            url, json=schedule, headers={"Authorization": access_token}
        )
        assert response.status_code == 400

    @pytest.mark.parametrize("key", ["warehouse_path", "flags", "image"])
    def test_create_schedule_missing_config_keys(self, client, access_token, key):
        schedule = {
            "name": "wikipedia_bm_test",
            "category": "wikipedia",
            "enabled": False,
            "tags": ["full"],
            "language": {
                "code": "bm",
                "name_en": "Bambara",
                "name_native": "Bamanankan",
            },
            "config": {
                "task_name": "phet",
                "warehouse_path": "/phet",
                "flags": {},
                "image": {"name": "openzim/phet", "tag": "latest"},
            },
        }

        del schedule["config"][key]
        url = "/schedules/"
        response = client.post(
            url, json=schedule, headers={"Authorization": access_token}
        )
        assert response.status_code == 400

    # exluding empty dict as it is invalid for PATCH but not for POST
    @pytest.mark.parametrize("update", [bpu for bpu in bad_patch_updates if bpu])
    def test_create_schedule_errors(self, client, access_token, update):
        schedule = {
            "name": "wikipedia_bm_test",
            "category": "wikipedia",
            "enabled": False,
            "tags": ["full"],
            "language": {
                "code": "bm",
                "name_en": "Bambara",
                "name_native": "Bamanankan",
            },
            "config": {
                "task_name": "phet",
                "warehouse_path": "/phet",
                "flags": {},
                "image": {"name": "openzim/phet", "tag": "latest"},
            },
        }

        schedule.update(update)

        url = "/schedules/"
        response = client.post(
            url, json=schedule, headers={"Authorization": access_token}
        )
        assert response.status_code == 400

    def test_unauthorized(self, client, access_token):
        schedule = {"name": "wikipedia_bm_test2"}
        url = "/schedules/"
        response = client.post(url, json=schedule)
        assert response.status_code == 401
        assert response.get_json() == {"error": "token invalid"}


class TestScheduleGet:
    def test_get_schedule_with_name(self, client, schedule):

        url = "/schedules/{}".format(schedule["name"])
        response = client.get(url)
        assert response.status_code == 200

        del schedule["_id"]
        schedule["config"].update(command_information_for(schedule["config"]))
        assert response.get_json() == schedule


class TestSchedulePatch:
    def _patch_schedule_via_key_with(self, client, access_token, update, schedule, key):

        if "name" in update.keys():
            update["name"] += str(uuid4())

        url = "/schedules/{}".format(schedule[key])
        response = client.patch(
            url, json=update, headers={"Authorization": access_token}
        )
        assert response.status_code == 204

        if key == "name" and "name" in update.keys():
            url = "/schedules/{}".format(update["name"])
        response = client.get(url, headers={"Authorization": access_token})
        assert response.status_code == 200

        document = response.get_json()
        document.update(update)
        assert response.get_json() == document

    @pytest.mark.parametrize("update", good_patch_updates)
    def test_patch_schedule_via_id_with(self, client, access_token, update, schedule):

        self._patch_schedule_via_key_with(
            client, access_token, update, schedule, "name"
        )

    @pytest.mark.parametrize("update", good_patch_updates)
    def test_patch_schedule_via_name_with(self, client, access_token, update, schedule):

        self._patch_schedule_via_key_with(
            client, access_token, update, schedule, "name"
        )

    def _patch_schedule_via_id_with_errors(
        self, client, access_token, update, schedule, key
    ):

        url = "/schedules/{}".format(schedule[key])
        response = client.patch(
            url, json=update, headers={"Authorization": access_token}
        )
        assert response.status_code == 400

    @pytest.mark.parametrize("update", bad_patch_updates)
    def test_patch_schedule_via_id_with_errors(
        self, client, access_token, update, schedule
    ):
        self._patch_schedule_via_id_with_errors(
            client, access_token, update, schedule, "name"
        )

    @pytest.mark.parametrize("update", bad_patch_updates)
    def test_patch_schedule_via_name_with_errors(
        self, client, access_token, update, schedule
    ):
        self._patch_schedule_via_id_with_errors(
            client, access_token, update, schedule, "name"
        )

    def test_patch_schedule_duplicate_name(self, client, access_token, schedules):

        update = {"name": "wikipedia_bm_all_nopic"}  # this one exists in fixtures
        url = "/schedules/wikipedia_fr_all_maxi"
        response = client.patch(
            url, json=update, headers={"Authorization": access_token}
        )
        assert response.status_code == 400

    def test_unauthorized(self, client, access_token, schedules):
        language = {"name": "new_name"}
        url = "/schedules/youtube_fr_all_novid"
        response = client.patch(url, json=language)
        assert response.status_code == 401
        assert response.get_json() == {"error": "token invalid"}


class TestScheduleDelete:
    def test_delete_schedule(self, client, access_token, schedule):
        """Test delete schedule with id or name"""

        url = "/schedules/{}".format(schedule["name"])
        response = client.delete(url, headers={"Authorization": access_token})
        assert response.status_code == 204

    def test_unauthorized(self, client, access_token, schedule):
        url = "/schedules/{}".format(schedule["name"])
        response = client.delete(url)
        assert response.status_code == 401
        assert response.get_json() == {"error": "token invalid"}
