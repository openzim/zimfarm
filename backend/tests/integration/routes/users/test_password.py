import pytest


class TestPassword:
    @pytest.mark.parametrize(
        "username, create_new_user, use_admin_token, expected_status_code,"
        "current_password",
        [
            (
                "user_123",
                True,
                True,
                204,
                None,
            ),  # set password as admin without current password
            (
                "user_124",
                True,
                False,
                204,
                "some-password",
            ),  # set password as user with current password
            (
                "user_125",
                True,
                False,
                401,
                "some-wrong-password",
            ),  # set password as user but wrong current password
            (
                "user_126",
                True,
                False,
                400,
                None,
            ),  # set password as user but no current password supplied
            (
                "user_does_not_exists",
                False,
                True,
                404,
                None,
            ),  # set password as admin for user which does not exists
            (
                "del_user_1",
                False,
                True,
                404,
                None,
            ),  # set password as admin for user which has been marked as deleted
        ],
    )
    def test_update_password(
        self,
        client,
        access_token,
        users,
        deleted_users,
        make_user,
        make_access_token,
        username,
        create_new_user,
        use_admin_token,
        expected_status_code,
        current_password,
    ):
        if create_new_user:
            make_user(username=username, role="editor")
        document = {
            "new": "my-new-password",
        }
        if current_password:
            document["current"] = current_password
        url = f"/users/{username}/password"
        response = client.patch(
            url,
            json=document,
            headers={
                "Authorization": (
                    access_token if use_admin_token else make_access_token(username)
                )
            },
        )
        assert response.status_code == expected_status_code
