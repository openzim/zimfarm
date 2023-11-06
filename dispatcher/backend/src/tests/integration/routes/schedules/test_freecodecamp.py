class TestFreeCodeCamp:
    def test_create_freecodecamp_schedule_ok(
        self, client, access_token, garbage_collector
    ):
        schedule = {
            "name": "fcc_javascript_test_ok",
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
                "flags": {
                    "course": ("somecourse"),
                    "language": "eng",
                    "name": "acourse",
                    "title": "a title",
                    "description": "a description",
                },
                "resources": {"cpu": 3, "memory": 1024, "disk": 0},
            },
            "periodicity": "quarterly",
        }

        url = "/schedules/"
        response = client.post(
            url, json=schedule, headers={"Authorization": access_token}
        )
        response_data = response.get_json()
        print(response_data)
        if "_id" in response_data:
            garbage_collector.add_schedule_id(response_data["_id"])
        assert response.status_code == 201

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

    def test_create_freecodecamp_schedule_ko(
        self, client, access_token, garbage_collector
    ):
        schedule = {
            "name": "fcc_javascript_test_ko",
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
                "flags": {
                    "course": ("somecourse"),
                    "language": "eng",
                    "name": "acourse",
                    "title": "a title",
                    "description": (
                        "a description which is way way way way way way way way way "
                        "way way way way way way way way way too long"
                    ),
                },
                "resources": {"cpu": 3, "memory": 1024, "disk": 0},
            },
            "periodicity": "quarterly",
        }

        url = "/schedules/"
        response = client.post(
            url, json=schedule, headers={"Authorization": access_token}
        )
        response_data = response.get_json()
        print(response_data)
        if "_id" in response_data:
            garbage_collector.add_schedule_id(response_data["_id"])
        assert response.status_code == 400
        assert "error_description" in response_data
        assert "description" in response_data["error_description"]
        assert (
            "Longer than maximum length 80."
            in response_data["error_description"]["description"]
        )
