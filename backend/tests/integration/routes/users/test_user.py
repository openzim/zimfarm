import pytest


class TestUsersList:
    def test_list_no_auth(self, client, users):
        url = "/users/"
        response = client.get(url)
        assert response.status_code == 401

    def test_list_no_param(self, client, access_token, users):
        url = "/users/"
        response = client.get(url, headers={"Authorization": access_token})
        assert response.status_code == 200

        response_json = response.get_json()
        print(response_json)
        assert "items" in response_json
        assert "meta" in response_json
        assert response_json["meta"]["count"] == len(users)
        assert len(response_json["items"]) == len(users)
        for item in response_json["items"]:
            assert set(item.keys()) == {
                "username",
                "email",
                "role",
            }

    @pytest.mark.parametrize(
        "skip, limit, expected", [(0, 1, 1), (1, 10, 4), (0, 100, 5)]
    )
    def test_list_with_param(self, client, access_token, users, skip, limit, expected):
        url = "/users/?skip={}&limit={}".format(skip, limit)
        response = client.get(url, headers={"Authorization": access_token})
        assert response.status_code == 200

        response_json = response.get_json()
        assert "items" in response_json
        assert len(response_json["items"]) == expected

    @pytest.mark.parametrize("skip, limit", [("", 10), (5, "abc")])
    def test_list_bad_param(self, client, access_token, users, skip, limit):
        url = "/users/?skip={}&limit={}".format(skip, limit)
        response = client.get(url, headers={"Authorization": access_token})
        assert response.status_code == 400

    def test_list_with_deleted_users(self, client, access_token, users, deleted_users):
        url = "/users/"
        response = client.get(url, headers={"Authorization": access_token})
        assert response.status_code == 200
        response_json = response.get_json()
        assert response_json["meta"]["count"] == len(users)
        assert len(response_json["items"]) == len(users)


class TestUser:
    @pytest.mark.parametrize(
        "username, exists, deleted",
        [
            ("user_0", True, False),
            ("user_1", True, False),
            ("user_4", True, False),
            ("user_6", False, False),
            ("del_user_0", False, True),
        ],
    )
    def test_get_one_user(
        self, client, access_token, users, deleted_users, username, exists, deleted
    ):
        url = f"/users/{username}"
        response = client.get(url, headers={"Authorization": access_token})

        if not exists or deleted:
            assert response.status_code == 404
        else:
            assert response.status_code == 200
            response_json = response.get_json()
            assert "username" in response_json

    @pytest.mark.parametrize(
        "username, exists, deleted",
        [
            ("user_0", True, False),
            ("user_1", True, False),
            ("user_4", True, False),
            ("user_6", False, False),
            ("del_user_0", False, True),
        ],
    )
    def test_patch_one_user_email(
        self, client, access_token, users, deleted_users, username, exists, deleted
    ):
        url = f"/users/{username}"
        update = {"email": f"{username}new@acme.com"}
        response = client.patch(
            url, json=update, headers={"Authorization": access_token}
        )

        if not exists or deleted:
            assert response.status_code == 404
        else:
            assert response.status_code == 204

    def test_delete_one_user(self, client, access_token, make_user, users):
        username = "ac34901547d5"
        make_user(username=username)
        url = f"/users/{username}"
        response = client.delete(url, headers={"Authorization": access_token})
        assert response.status_code == 204

        url = "/users/"
        response = client.get(url, headers={"Authorization": access_token})
        assert response.status_code == 200
        response_json = response.get_json()
        assert response_json["meta"]["count"] == len(users)
        assert len(response_json["items"]) == len(users)

        # we still shouldn't be able to create a user with same username
        document = {
            "username": username,
            "password": "my-long-password",
            "email": "user_create_test@kiwix.org",
            "role": "manager",
        }
        url = "/users/"
        response = client.post(
            url, json=document, headers={"Authorization": access_token}
        )
        assert response.status_code == 400
        response_json = response.get_json()
        assert "error" in response_json
        assert response_json["error"] == "User already exists"

    def test_create_user_ok(self, client, access_token, cleanup_create_test):
        document = {
            "username": "user_create_test",
            "password": "my-long-password",
            "email": "user_create_test@kiwix.org",
            "role": "manager",
        }
        url = "/users/"
        response = client.post(
            url, json=document, headers={"Authorization": access_token}
        )
        assert response.status_code == 200

        url = "/users/{}".format(document["username"])
        response = client.get(url, headers={"Authorization": access_token})

        assert response.status_code == 200

    def test_create_user_duplicate(self, client, access_token, users):
        document = {
            "username": "user_0",
            "password": "my-long-password",
            "email": "user_create_test@kiwix.org",
            "role": "manager",
        }
        url = "/users/"
        response = client.post(
            url, json=document, headers={"Authorization": access_token}
        )
        assert response.status_code == 400
        response_json = response.get_json()
        assert "error" in response_json
        assert response_json["error"] == "User already exists"
