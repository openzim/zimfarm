class TestFreeCodeCamp:
    def test_create_freecodecamp_schedule(
        self, client, access_token, garbage_collector
    ):
        schedule = {
            "name": "fcc_javascript_test",
            "category": "freecodecamp",
            "enabled": False,
            "tags": [],
            "language": {"code": "fr", "name_en": "French", "name_native": "Français"},
            "config": {
                "task_name": "freecodecamp",
                "warehouse_path": "/freecodecamp",
                "image": {"name": "openzim/freecodecamp", "tag": "1.0.0"},
                "monitor": False,
                "platform": None,
                "flags": {},
                "resources": {"cpu": 3, "memory": 1024, "disk": 0},
            },
            "periodicity": "quarterly",
        }

        url = "/schedules/"
        response = client.post(
            url, json=schedule, headers={"Authorization": access_token}
        )
        assert response.status_code == 201
        response_data = response.get_json()
        garbage_collector.add_schedule_id(response_data["_id"])

        patch_data = {
            "enabled": True,
            "flags": {
                "output-dir": "/output",
                "course": (
                    "regular-expressions,basic-javascript,basic-data-structures,"
                    "debugging,functional-programming,object-oriented-programming,"
                    "basic-algorithm-scripting,intermediate-algorithm-scripting,"
                    "javascript-algorithms-and-data-structures-projects"
                ),
                "language": "eng",
                "name": "fcc_en_javascript",
                "title": "freeCodeCamp Javascript",
                "description": "FCC Javascript Courses",
            },
        }

        url = f"/schedules/{schedule['name']}"
        response = client.patch(
            url, json=patch_data, headers={"Authorization": access_token}
        )
        assert response.status_code == 204
