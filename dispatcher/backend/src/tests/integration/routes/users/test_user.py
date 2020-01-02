import pytest


class TestUsersList:
    def test_list_no_auth(self, client, users):
        url = "/users/"
        response = client.get(url)
        assert response.status_code == 401

    def test_list_no_param(self, client, users, access_token):

        url = "/users/"
        response = client.get(url, headers={"Authorization": access_token})
        assert response.status_code == 200

        response_json = response.get_json()
        assert "items" in response_json
        assert len(response_json["items"]) == 5
        for item in response_json["items"]:
            assert set(item.keys()) == {
                "username",
                "role",
            }

    @pytest.mark.parametrize(
        "skip, limit, expected", [(0, 1, 1), (1, 10, 4), (0, 100, 5)]
    )
    def test_list_with_param(self, client, users, access_token, skip, limit, expected):

        url = "/users/?skip={}&limit={}".format(skip, limit)
        response = client.get(url, headers={"Authorization": access_token})
        assert response.status_code == 200

        response_json = response.get_json()
        assert "items" in response_json
        assert len(response_json["items"]) == expected

    @pytest.mark.parametrize("skip, limit", [("", 10), (5, "abc")])
    def test_list_bad_param(self, client, schedules, access_token, skip, limit):

        url = "/users/?skip={}&limit={}".format(skip, limit)
        response = client.get(url, headers={"Authorization": access_token})
        assert response.status_code == 400
