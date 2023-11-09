class TestZimit:
    def test_create_zimit_schedule_ok(self, client, access_token, garbage_collector):
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

        url = "/schedules/"
        response = client.post(
            url, json=schedule, headers={"Authorization": access_token}
        )
        response_data = response.get_json()
        print(response_data)
        if "_id" in response_data:
            garbage_collector.add_schedule_id(response_data["_id"])
        assert response.status_code == 201

    # below test is green only if ZIMIT_DISABLE_ZIM_FILENAME_CHECK is set
    # def test_create_zimit_schedule_bad_name_ok(
    #     self, client, access_token, garbage_collector
    # ):
    #     schedule = {
    #         "name": "zimit_test_bad_name_ok",
    #         "category": "other",
    #         "enabled": False,
    #         "tags": [],
    #         "language": {
    #             "code": "fr",
    #             "name_en": "French",
    #             "name_native": "Français"
    #         },
    #         "config": {
    #             "task_name": "zimit",
    #             "warehouse_path": "/other",
    #             "image": {"name": "openzim/zimit", "tag": "1.0.0"},
    #             "monitor": False,
    #             "platform": None,
    #             "flags": {
    #                 "name": "acme",
    #                 "url": "https://www.acme.com",
    #                 "zim-file": "bad_name",
    #             },
    #             "resources": {"cpu": 3, "memory": 1024, "disk": 0},
    #         },
    #         "periodicity": "quarterly",
    #     }

    #     url = "/schedules/"
    #     response = client.post(
    #         url, json=schedule, headers={"Authorization": access_token}
    #     )
    #     response_data = response.get_json()
    #     print(response_data)
    #     if "_id" in response_data:
    #         garbage_collector.add_schedule_id(response_data["_id"])
    #     assert response.status_code == 201

    # below test becomes red if ZIMIT_DISABLE_ZIM_FILENAME_CHECK is set
    def test_create_zimit_schedule_bad_name_nok(
        self, client, access_token, garbage_collector
    ):
        schedule = {
            "name": "zimit_test_bad_name_nok",
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
                    "zim-file": "bad_name",
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
        assert "zim-file" in response_data["error_description"]
