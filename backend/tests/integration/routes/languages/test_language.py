import pytest


class TestLanguagesList:
    def test_list_languages_no_param(self, client, schedules):
        """Test list languages"""

        url = "/languages/"
        response = client.get(url)
        assert response.status_code == 200

        response_json = response.get_json()
        assert "items" in response_json
        assert len(response_json["items"]) == 3
        for item in response_json["items"]:
            assert isinstance(item["code"], str)
            assert isinstance(item["name_en"], str)
            assert isinstance(item["name_native"], str)

    @pytest.mark.parametrize(
        "skip, limit, expected", [(0, 1, 1), (1, 10, 2), (0, 100, 3)]
    )
    def test_list_languages_with_param(self, client, schedules, skip, limit, expected):
        """Test list languages with skip and limit"""

        url = "/languages/?skip={}&limit={}".format(skip, limit)
        response = client.get(url)
        assert response.status_code == 200

        response_json = response.get_json()
        assert "items" in response_json
        assert len(response_json["items"]) == expected

    @pytest.mark.parametrize("skip, limit", [("", 10), (5, "abc")])
    def test_list_languages_with_bad_param(self, client, schedules, skip, limit):
        """Test list languages with skip and limit"""

        url = "/languages/?skip={}&limit={}".format(skip, limit)
        response = client.get(url)
        assert response.status_code == 400
