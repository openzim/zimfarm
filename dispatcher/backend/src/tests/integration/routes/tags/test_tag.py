import pytest


class TestTagsList:
    def test_list_tags_no_param(self, client, schedules):
        """Test list tags"""

        url = "/tags/"
        response = client.get(url)
        assert response.status_code == 200

        response_json = response.get_json()
        assert "items" in response_json
        assert len(response_json["items"]) == 4
        for item in response_json["items"]:
            assert isinstance(item, str)

    @pytest.mark.parametrize(
        "skip, limit, expected", [(0, 1, 1), (1, 10, 3), (0, 100, 4)]
    )
    def test_list_tags_with_param(self, client, schedules, skip, limit, expected):
        """Test list languages with skip and limit"""

        url = "/tags/?skip={}&limit={}".format(skip, limit)
        response = client.get(url)
        assert response.status_code == 200

        response_json = response.get_json()
        assert "items" in response_json
        assert len(response_json["items"]) == expected

    @pytest.mark.parametrize("skip, limit", [("", 10), (5, "abc")])
    def test_list_tags_bad_param(self, client, schedules, skip, limit):
        """Test list languages with skip and limit"""

        url = "/tags/?skip={}&limit={}".format(skip, limit)
        response = client.get(url)
        assert response.status_code == 400
