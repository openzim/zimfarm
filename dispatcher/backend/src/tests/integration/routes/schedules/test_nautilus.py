from collections import namedtuple
from typing import List

import pytest
from utils_for_tests import update_dict

from common import constants


class TestZimit:
    mod = namedtuple("Modification", ["key_path", "new_value"])

    @pytest.mark.parametrize(
        "modifications, relaxed_schema, succeeds",
        [
            (
                [mod(key_path="name", new_value="nautilus_test_good_name_not_relaxed")],
                False,
                True,
            ),
            (
                [mod(key_path="name", new_value="nautilus_test_good_name_relaxed")],
                True,
                True,
            ),
            (
                [
                    mod(
                        key_path="name", new_value="nautilus_test_bad_name_not_relaxed"
                    ),
                    mod(key_path="config.flags.zim-file", new_value="bad_name"),
                ],
                False,
                False,
            ),
            (
                [
                    mod(key_path="name", new_value="nautilus_test_bad_name_relaxed"),
                    mod(key_path="config.flags.zim-file", new_value="bad_name"),
                ],
                True,
                True,
            ),
        ],
    )
    def test_create_nautilus_schedule_generic(
        self,
        client,
        access_token,
        garbage_collector,
        modifications: List[mod],
        relaxed_schema: bool,
        succeeds: bool,
    ):
        constants.NAUTILUS_USE_RELAXED_SCHEMA = relaxed_schema
        schedule = {
            "name": "nautilus_test_ok",
            "category": "other",
            "enabled": False,
            "tags": [],
            "language": {"code": "fr", "name_en": "French", "name_native": "Français"},
            "config": {
                "task_name": "nautilus",
                "warehouse_path": "/other",
                "image": {"name": "openzim/nautilus", "tag": "1.0.0"},
                "monitor": False,
                "platform": None,
                "flags": {
                    "name": "acme",
                    "collection": "https://www.acme.com",
                    "zim-file": "acme_en_all_{period}.zim",
                },
                "resources": {"cpu": 3, "memory": 1024, "disk": 0},
            },
            "periodicity": "quarterly",
        }
        for modification in modifications:
            update_dict(schedule, modification.key_path, modification.new_value)
        url = "/schedules/"
        response = client.post(
            url, json=schedule, headers={"Authorization": access_token}
        )
        response_data = response.get_json()
        if "_id" in response_data:
            garbage_collector.add_schedule_id(response_data["_id"])
        if succeeds:
            assert response.status_code == 201
        else:
            assert response.status_code == 400
            assert "error_description" in response_data
            assert "zim-file" in response_data["error_description"]
