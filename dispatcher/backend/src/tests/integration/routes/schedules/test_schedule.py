import json
from copy import deepcopy
from uuid import uuid4

import pytest
from utils_for_tests import patch_dict

from utils.offliners import expanded_config

ONE_GiB = 2**30
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
    {
        "task_name": "mwoffliner",
    },
    {
        "task_name": "phet",
        "flags": {},
        "image": {"name": "openzim/phet", "tag": "1.1.2"},
    },
    {"flags": {"mwUrl": "https://fr.wikipedia.org", "adminEmail": "hello@test.de"}},
    {"warehouse_path": "/phet"},
    {"image": {"name": "openzim/mwoffliner", "tag": "1.12.2"}},
    {"artifacts_globs": ["*.json", "**/*.json"]},
    {"resources": {"cpu": 3, "memory": MIN_RAM, "disk": ONE_GiB}},
    {
        "task_name": "gutenberg",
        "warehouse_path": "/gutenberg",
        "flags": {},
        "image": {"name": "openzim/gutenberg", "tag": "1.1.2"},
        "resources": {"cpu": 3, "memory": MIN_RAM, "disk": ONE_GiB},
    },
    {"name": "new_name"},
]

bad_patch_updates = [
    # Empty patch not allowed
    {},
    # wrong languages combinations
    {"language": {"name_en": "Bambara", "name_native": "Bamanankan"}},
    {"language": {"code": "bm", "name_en": "", "name_native": "Bamanankan"}},
    {"language": {"code": "bm", "name_en": "Bambara"}},
    # enabled flag must be a boolean, not a string
    {"enabled": "False"},
    # illegal category
    {"category": "ubuntu"},
    # empty tags not allowed
    {"tags": ""},
    # tags must be strings
    {"tags": ["full", 1]},
    # tags must be a list
    {"tags": "full,small"},
    # name cannot be empty
    {"name": ""},
    # config cannot be empty
    {"config": ""},
    # mwoffliner does not supports empty flags
    {"flags": {}},
    # cannot change only offliner, image must be changed as well
    {"task_name": "phet", "flags": {}},
    # cannot change only image name, offliner must be changed as well
    {"flags": {}, "image": {"name": "openzim/phet", "tag": "latest"}},
    # illegal offliner name
    {
        "task_name": "hop",
        "flags": {},
        "image": {"name": "openzim/hop", "tag": "latest"},
    },
    # wrong warehouse_path
    {
        "warehouse_path": "/ubuntu",
    },
    # wrong mwUrl flag for phet
    {
        "task_name": "phet",
        "flags": {"mwUrl": "http://fr.wikipedia.org"},
        "image": {"name": "openzim/phet", "tag": "latest"},
    },
    # image name not aligned with task name
    {
        "task_name": "gutenberg",
        "flags": {},
        "image": {"name": "openzim/youtube", "tag": "latest"},
    },
    # bad cpu value
    {
        "resources": {"cpu": -1, "memory": MIN_RAM, "disk": ONE_GiB},
    },
    # bad mem value
    {
        "resources": {"cpu": 3, "memory": -1, "disk": ONE_GiB},
    },
    # bad disk value
    {
        "resources": {"cpu": 3, "memory": MIN_RAM, "disk": -1},
    },
    # one resource missing
    {
        "resources": {"cpu": 3, "memory": MIN_RAM},
    },
    # illegal characters in name
    {"name": "new\u0000name"},
    # illegal characters in mwUrl
    {
        "flags": {
            "mwUrl": "https://fr.wiki\u0000pedia.org",
            "adminEmail": "hello@test.de",
        }
    },
    # illegal characters in adminEmail
    {
        "flags": {
            "mwUrl": "https://fr.wikipedia.org",
            "adminEmail": "he\u0000llo@test.de",
        }
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
            assert isinstance(item["is_requested"], bool)

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
                "name": "wikipedia_bm_create_test",
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
                    "platform": None,
                    "resources": {"cpu": 3, "memory": MIN_RAM, "disk": ONE_GiB},
                    "monitor": False,
                },
                "notification": {},
            },
            {
                "name": "gutenberg_mul_create_test",
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
                    "platform": None,
                    "resources": {"cpu": 3, "memory": MIN_RAM, "disk": ONE_GiB},
                    "monitor": False,
                    "artifacts_globs": ["**/*.json"],
                },
                "notification": {},
            },
        ],
    )
    def test_create_schedule_ok(
        self, client, access_token, document, cleanup_create_test
    ):
        url = "/schedules/"
        response = client.post(
            url, json=document, headers={"Authorization": access_token}
        )
        assert response.status_code == 201

        url = "/schedules/{}".format(document["name"])
        response = client.get(url, headers={"Authorization": access_token})

        assert response.status_code == 200

        response_json = response.get_json()
        document["config"] = expanded_config(document["config"])

        # these properties are generated server side, we just check they are present
        assert "duration" in response_json
        assert "default" in response_json["duration"]
        assert "workers" in response_json["duration"]
        assert not response_json["duration"]["available"]
        assert "most_recent_task" in response_json
        response_json.pop("duration", None)
        response_json.pop("most_recent_task", None)
        assert "is_requested" in response_json
        assert response_json["is_requested"] is False
        response_json.pop("is_requested")

        assert response_json == document

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
                "monitor": False,
                "platform": None,
                "resources": {"cpu": 3, "memory": 1024, "disk": 0},
            },
            "periodicity": "quarterly",
        }

        del schedule[key]
        url = "/schedules/"
        response = client.post(
            url, json=schedule, headers={"Authorization": access_token}
        )
        response_data = response.get_json()
        assert response.status_code == 400
        assert "error_description" in response_data
        assert key in response_data["error_description"]
        assert (
            "Missing data for required field."
            in response_data["error_description"][key]
        )

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
                "monitor": False,
                "platform": None,
                "resources": {"cpu": 3, "memory": 1024, "disk": 0},
            },
            "periodicity": "quarterly",
        }

        del schedule["config"][key]
        url = "/schedules/"
        response = client.post(
            url, json=schedule, headers={"Authorization": access_token}
        )
        response_data = response.get_json()
        assert response.status_code == 400
        assert "error_description" in response_data
        assert "config" in response_data["error_description"]
        assert key in response_data["error_description"]["config"]
        assert (
            "Missing data for required field."
            in response_data["error_description"]["config"][key]
        )

    def test_create_schedule_flags_ko(self, client, access_token):
        schedule = {
            "name": "ifixit flags ko",
            "category": "ifixit",
            "enabled": False,
            "tags": [],
            "language": {
                "code": "en",
                "name_en": "English",
                "name_native": "English",
            },
            "config": {
                "task_name": "ifixit",
                "warehouse_path": "/ifixit",
                "flags": {},
                "image": {"name": "openzim/ifixit", "tag": "latest"},
                "monitor": False,
                "platform": "ifixit",
                "resources": {"cpu": 3, "memory": 1024, "disk": 0},
            },
            "periodicity": "quarterly",
        }

        url = "/schedules/"
        response = client.post(
            url, json=schedule, headers={"Authorization": access_token}
        )
        response_data = response.get_json()
        assert response.status_code == 400
        assert "error_description" in response_data
        assert "language" in response_data["error_description"]
        assert (
            "Missing data for required field."
            in response_data["error_description"]["language"]
        )

    def test_image_names(self, client, schedule, access_token):
        url = "/schedules/{}/image-names".format(schedule["name"])
        response = client.get(
            url,
            headers={"Authorization": access_token},
            query_string={"hub_name": "openzim/mwoffliner"},
        )
        assert response.status_code == 200
        response = json.loads(response.data)
        assert len(response["items"]) > 0
        for item in response["items"]:
            assert isinstance(item, str)

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

        schedule["config"] = expanded_config(schedule["config"])

        response_json = response.get_json()
        # these properties are generated server side, we just check they are present
        assert "duration" in response_json
        assert "default" in response_json["duration"]
        assert "workers" in response_json["duration"]
        assert not response_json["duration"]["available"]
        assert "most_recent_task" in response_json
        response_json.pop("duration", None)
        response_json.pop("most_recent_task", None)
        schedule.pop("_id")
        assert "is_requested" in response_json
        assert response_json["is_requested"] is False
        response_json.pop("is_requested")

        assert response_json == schedule


class TestSchedulePatch:
    @pytest.mark.parametrize("update", good_patch_updates)
    def test_patch_schedule_via_name_with(self, client, access_token, update, schedule):
        if "name" in update.keys():
            update["name"] += str(uuid4())

        url = "/schedules/{}".format(schedule["name"])
        response = client.patch(
            url, json=update, headers={"Authorization": access_token}
        )
        assert response.status_code == 204

        if "name" in update.keys():
            url = "/schedules/{}".format(update["name"])
        response = client.get(url, headers={"Authorization": access_token})
        assert response.status_code == 200

        # let's reapply manually the changes that should have been done by the patch
        # so that we can confirm it has been done
        document = response.get_json()

        update_patch = {}
        config_keys = [
            "task_name",
            "warehouse_path",
            "image",
            "resources",
            "platform",
            "flags",
            "monitor",
            "artifacts_globs",
        ]
        for key, value in update.items():
            if key in config_keys:
                if "config" not in update_patch:
                    update_patch["config"] = {}
                update_patch["config"][key] = value
            else:
                update_patch[key] = value

        # handle special situation for config image name
        if (
            "config" in update_patch
            and "image" in update_patch["config"]
            and "name" in update_patch["config"]["image"]
        ):
            update_patch["config"]["image"]["name"] = (
                "ghcr.io/" + update_patch["config"]["image"]["name"]
            )

        patch_result = patch_dict(deepcopy(document), update_patch)
        assert document == patch_result

    @pytest.mark.parametrize("update", bad_patch_updates)
    def test_patch_schedule_via_name_with_errors(
        self, client, access_token, update, schedule
    ):
        url = "/schedules/{}".format(schedule["name"])
        response = client.patch(
            url, json=update, headers={"Authorization": access_token}
        )
        assert response.status_code == 400

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

    def test_patch_schedule_does_not_set_null_config_keys(
        self, client, access_token, schedule
    ):

        update = {"platform": None}
        url = "/schedules/{}".format(schedule["name"])
        response = client.patch(
            url, json=update, headers={"Authorization": access_token}
        )
        assert response.status_code == 204

        response = client.get(url, headers={"Authorization": access_token})
        assert response.status_code == 200

        document = response.get_json()

        assert "config" in document
        assert "platform" not in document["config"]

    def test_patch_schedule_remove_null_config_keys(
        self, client, access_token, schedule
    ):

        update = {"platform": "ifixit"}
        url = "/schedules/{}".format(schedule["name"])
        response = client.patch(
            url, json=update, headers={"Authorization": access_token}
        )
        assert response.status_code == 204

        response = client.get(url, headers={"Authorization": access_token})
        assert response.status_code == 200

        document = response.get_json()

        assert "config" in document
        assert "platform" in document["config"]
        assert document["config"]["platform"] == "ifixit"

        update = {"platform": None}
        url = "/schedules/{}".format(schedule["name"])
        response = client.patch(
            url, json=update, headers={"Authorization": access_token}
        )
        assert response.status_code == 204

        response = client.get(url, headers={"Authorization": access_token})
        assert response.status_code == 200

        document = response.get_json()

        assert "config" in document
        assert "platform" not in document["config"]


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


class TestScheduleBackup:
    def test_schedule_backup(self, client, access_token, schedules):
        """Test get a backup of all schedules"""
        response = client.get(
            "/schedules/backup/", headers={"Authorization": access_token}
        )
        assert response.status_code == 200
        schedules_retrieved = response.get_json()
        assert type(schedules_retrieved) is list
        for schedule_retrieved in schedules_retrieved:
            assert "most_recent_task" not in schedule_retrieved
