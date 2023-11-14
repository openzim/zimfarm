from dataclasses import dataclass
from typing import List

import pytest

from common import constants


def update_dict(dict: dict, key_path: str, new_value: any):
    # Split the key path into individual keys
    keys = key_path.split(".")

    # Initialize a reference to the nested dictionary
    current_dict = dict

    # Navigate through the nested structure
    for key in keys[:-1]:
        current_dict = current_dict[key]

    # Update the value using the last key
    current_dict[keys[-1]] = new_value


class TestZimit:
    @dataclass
    class Modification:
        key_path: str
        new_value: str

    @pytest.mark.parametrize(
        "modifications, relaxed_schema, succeeds",
        [
            (
                [
                    Modification(
                        key_path="name", new_value="zimit_test_good_name_not_relaxed"
                    )
                ],
                False,
                True,
            ),
            (
                [
                    Modification(
                        key_path="name", new_value="zimit_test_good_name_relaxed"
                    )
                ],
                True,
                True,
            ),
            (
                [
                    Modification(
                        key_path="name", new_value="zimit_test_bad_name_not_relaxed"
                    ),
                    Modification(
                        key_path="config.flags.zim-file", new_value="bad_name"
                    ),
                ],
                False,
                False,
            ),
            (
                [
                    Modification(
                        key_path="name", new_value="zimit_test_bad_name_relaxed"
                    ),
                    Modification(
                        key_path="config.flags.zim-file", new_value="bad_name"
                    ),
                ],
                True,
                True,
            ),
        ],
    )
    def test_create_zimit_schedule_generic(
        self,
        client,
        access_token,
        garbage_collector,
        modifications: List[Modification],
        relaxed_schema: bool,
        succeeds: bool,
    ):
        constants.ZIMIT_USE_RELAXED_SCHEMA = relaxed_schema
        schedule = {
            "name": "zimit_test_ok",
            "category": "other",
            "enabled": False,
            "tags": [],
            "language": {"code": "fr", "name_en": "French", "name_native": "Français"},
            "config": {
                "task_name": "zimit",
                "warehouse_path": "/other",
                "image": {"name": "openzim/zimit", "tag": "1.0.0"},
                "monitor": False,
                "platform": None,
                "flags": {
                    "name": "acme",
                    "url": "https://www.acme.com",
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
