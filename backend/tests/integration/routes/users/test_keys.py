import pytest

public_key_rsa_4096 = (
    "AAAAB3NzaC1yc2EAAAADAQABAAACAQDtYGK/4lDEQAlf/ncwmhoc9IQOv8sYWSrIGkUPM/G/tsTz0EsrVU"
    "t2bVPTviJvIfYIIZqeDuDPWRepjl5r38mAPWs/VFSNkM7ObJPYMx+nUcggfC3Z9NApxdd/wX6AQL4mH/+a"
    "B1c5aUgXLfnV8uz+tcEo8lyM3zkEuSw5WbYZBhAyGdmj11tKxxZpA8KhkV8SrLny7wiLsGof+IbIYIGGh9"
    "HDGwGvHZbu6Oj+i4SXzuC+oRMPAkPZKrp/AGcglE4wIAXQ33dDy0tUrfmsq7UguEG0g2z1m55XxMXB1G/y"
    "YNl6/thPOvlb2cZV0uz3ku1FOf2J+TTudmOrGmehAd7vY2lFD3UCZDNOuscKkZ5oCkmiENve9jwVb1DHnq"
    "G2nSoyCAunsm6xd6jBsMaowslpdT10L65YFRBXexjtsUL97kdI2iBziN8Qdb2xeuFbgyCaV5MUQQstH8qA"
    "R5HTyajnwaiYl9Go4xOCY6M94UBa1EMtvMKKR2qwaQ4sxj15WoleDolmgpi47ZiEpOEiVyPGk7gpk7GiXL"
    "y6IsOZ9ZbZ2o6x0aM/5fwdEDiYbzjlG+QtTEbo2zFWBQ9yZVWulmzdwS97W7mKoB+Rn2sAbGSzxKssJQze"
    "AsCoso3lFjCdxYAaplQBpDuCXVC/Jgtf2XP2RlLBFX6t9RehsoIVPUd8qQ=="
)
public_key_rsa_2048 = (
    "AAAAB3NzaC1yc2EAAAADAQABAAABAQDEToJ0EFv1Z/FL3EhE10gA11eelGQpG0uHxdy9VOJhT/gvK8P16y"
    "PvF1w2Yb/wAHLEW/ztDTjZn1WlBVZUSXUrvok1fypt4xzXFZ2Y/EBHg41ue1aF9RwgEGoVaM/B3TCrx78e"
    "k7/0xACFGVYZ/wApBpstafPEiteVS3Lj+9nh8FKvvnVQvid4vKAayFLQ9RB31NvAXAMzgfyLj9RQWU1sDj"
    "GvtXPL+5gybo2dsDfyxEDYyJi5D7bJgg3tE4+tbaEky9jWlZ3gLtopJcq8QSEHJttHHsVYjvGQAaIzSySY"
    "/nokmw4BcTUi/eQVQrKGRKz5O+AX20BNRup0wtln9mJH"
)
fingerprint_rsa_2048 = "66b144e7237c9686f9e63cc80273c9a2"
public_key_rsa_1024 = (
    "AAAAB3NzaC1yc2EAAAADAQABAAAAgQC8KgzWm3uFMOToCSCt0XrTqPjaFpjRhtN/d7RMyg1e71iW1ATFwr"
    "+QwTBBmsIvIKjyaW6YyngVWpdGn2ljxM9UKfpysg1PqbkqqnrWBC1BK55p0iyqi+I7fBj5zAVE0M1Vh5j3"
    "SrMrheSTbcEFgz4DQ8zdq0HfqWVuNLXzcxkS2Q=="
)
public_key_ed25519 = (  # ssh-ed25519
    "AAAAC3NzaC1lZDI1NTE5AAAAIFS2Lv4WyT5r9H0ASs33MylhpH2fgl/17d3zviI1ezTs"
)
public_key_dsa = (  # ssh-dss
    "AAAAB3NzaC1kc3MAAACBAJbMbf6eyhrO+CByHs7Bdday/EfGCRWaX3Oqiauu5id6p/5Axsc8RZBZUEXpGB"
    "5pQPU7xqc6UDLme/5A6SgZPc+e8SBpQRElBXNU6LM57d5jIgH1WGPQi0/MzMTbU6WGu8CS9ErN3B4TFRKq"
    "Tf/2otlGqBLwUha2ewJLm9dkfBXdAAAAFQCuMjQ7OBQaU89FuMyEgkD0ESgb7wAAAIBxPW8f2bdZTH57I7"
    "nNTS8mxr0nvWCHoCvHkApwILfzChRgxkpxxF6Z5UvYG6TOHNoQK4iaha8Qcp5TSRddYvh9e+jTwpT6WQ9C"
    "eguzTA0scad8pT7Yt47lKVjdE9CTw3pO+v6J7+Wf4buLZw2DGSPs8FjqkGGBzvBqKW3Y0UsB8wAAAIAsl8"
    "Ng2ZcTsIrFbRpnbfSHIOI5A7GZgQhaKntC8Dn+MNFpUXGYze4BDJg3zjOiNNLAcALGqyhkGtg/kQwkBcla"
    "GfaEH8l0Esao7iyj9X3fwt+BUghJoGmWsBODbswbWYozJmwGQZMWlbuRdDkOc9jNaMqgBDQvIQ/j8m5haq"
    "68GA=="
)

auth_test_cases = [
    (
        None,
        None,
        "existing",
        401,
    ),  # do it without auth supplied => not authorized
    (
        "someone-else",
        "manager",
        "existing",
        401,
    ),  # do it with another user as a manager => insufficient rights
    (
        "someone-else",
        "admin",
        "dont-exists",
        404,
    ),  # do it with a non-existing user as an admin => not found
    (
        "someone-else",
        "manager",
        "dont-exists",
        401,
    ),  # do it with a non-existing user as a manager => insufficient rights
    (
        "someone-else",
        "admin",
        "deleted",
        404,
    ),  # do it with a deleted user as an admin => not found
]

list_test_cases = [
    (
        "self",
        "editor",
        "existing",
        200,
    ),  # do it with the user itself => this works
    (
        "someone-else",
        "admin",
        "existing",
        200,
    ),  # do it with another user as an administrator => this works
]


class TestUserKeysList:
    @pytest.mark.parametrize(
        "auth_username, auth_role, query_user, expected_status_code",
        auth_test_cases + list_test_cases,
    )
    def test_list_keys_auth(
        self,
        client,
        users,
        deleted_users,
        make_access_token,
        auth_username,
        auth_role,
        query_user,
        expected_status_code,
    ):
        if query_user == "existing":
            username = users[0]["username"]
        elif query_user == "deleted":
            username = deleted_users[0]["username"]
        else:
            username = "i_dont_exists"
        if auth_username == "self":
            auth_username = username
        url = f"/users/{username}/keys"
        if auth_username and auth_role:
            response = client.get(
                url,
                headers={"Authorization": make_access_token(auth_username, auth_role)},
            )
        else:
            response = client.get(url)
        assert response.status_code == expected_status_code


create_test_cases = [
    (
        "self",
        "editor",
        "existing1",
        201,
    ),  # do it with the user itself => this works
    (
        "someone-else",
        "admin",
        "existing2",
        201,
    ),  # do it with another user as an administrator => this works
]


class TestUserKeyCreate:
    @pytest.mark.parametrize(
        "auth_username, auth_role, query_user, expected_status_code",
        auth_test_cases + create_test_cases,
    )
    def test_create_user_key_auth(
        self,
        client,
        users,
        deleted_users,
        make_access_token,
        auth_username,
        auth_role,
        query_user,
        expected_status_code,
    ):
        if query_user == "existing1":
            username = users[1]["username"]
        elif query_user == "existing2":
            username = users[2]["username"]
        elif query_user == "deleted":
            username = deleted_users[0]["username"]
        else:
            username = "i_dont_exists"
        if auth_username == "self":
            auth_username = username
        url = f"/users/{username}/keys"
        document = {
            "name": "one-more-key",
            "key": public_key_rsa_2048,
        }
        if auth_username and auth_role:
            response = client.post(
                url,
                json=document,
                headers={"Authorization": make_access_token(auth_username, auth_role)},
            )
        else:
            response = client.post(url, json=document)
        assert response.status_code == expected_status_code

    @pytest.mark.parametrize(
        "key_name, public_key, expected_status_code, error_message",
        [
            ("rsa_1024", public_key_rsa_1024, 201, None),
            ("rsa_2048", f"ssh-rsa {public_key_rsa_2048}", 201, None),
            ("rsa_4096", f"ssh-rsa {public_key_rsa_4096} bob@whatever.com", 201, None),
            ("ed25519", public_key_ed25519, 400, "Invalid RSA key"),
            ("dsa", public_key_dsa, 400, "Invalid RSA key"),
            ("existing_fingerprint", None, 400, "SSH key already exists"),
        ],
    )
    def test_create_user_key_content(
        self,
        client,
        users,
        access_token,
        key,
        key_name,
        public_key,
        expected_status_code,
        error_message,
    ):
        username = users[0]["username"]
        url = f"/users/{username}/keys"
        document = {
            "name": key_name,
            "key": public_key if key_name != "existing_fingerprint" else key["key"],
        }
        response = client.post(
            url,
            json=document,
            headers={"Authorization": access_token},
        )
        assert response.status_code == expected_status_code
        if error_message:
            response_json = response.get_json()
            assert "error" in response_json
            assert response_json["error"] == error_message


get_test_cases = [
    (
        None,
        None,
        "existing",
        200,
    ),  # do it without auth supplied => this works
    (
        "someone-else",
        "manager",
        "existing",
        200,
    ),  # do it with another user as a manager => this works
    (
        "someone-else",
        "admin",
        "dont-exists",
        404,
    ),  # do it with a non-existing user as an admin => not found
    (
        "someone-else",
        "admin",
        "deleted",
        404,
    ),  # do it with a deleted user as an admin => not found
    (
        "self",
        "editor",
        "existing",
        200,
    ),  # do it with the user itself => this works
    (
        "someone-else",
        "admin",
        "existing",
        200,
    ),  # do it with another user as an administrator => this works
]


class TestUserKeyGet:
    @pytest.mark.parametrize(
        "auth_username, auth_role, query_user, expected_status_code",
        get_test_cases,
    )
    def test_get_user_key(
        self,
        client,
        users,
        deleted_users,
        make_access_token,
        key,
        auth_username,
        auth_role,
        query_user,
        expected_status_code,
    ):
        if query_user == "existing":
            username = users[0]["username"]
        elif query_user == "deleted":
            username = deleted_users[0]["username"]
        else:
            username = "i_dont_exists"
        if auth_username == "self":
            auth_username = username

        url = f"/users/{username}/keys/{key['fingerprint']}"
        if auth_username and auth_role:
            response = client.get(
                url,
                headers={"Authorization": make_access_token(auth_username, auth_role)},
            )
        else:
            response = client.get(url)
        assert response.status_code == expected_status_code
        if expected_status_code == 200:
            response_json = response.get_json()
            assert set(response_json.keys()) == {
                "username",
                "key",
                "type",
                "name",
            }

            assert response_json["username"] == username
            assert response_json["key"] == key["key"]
            assert response_json["type"] == key["type"]
            assert response_json["name"] == key["name"]


delete_test_cases = [
    (
        "self",
        "editor",
        "existing3",
        204,
    ),  # do it with the user itself => this works
    (
        "someone-else",
        "admin",
        "existing4",
        204,
    ),  # do it with another user as an administrator => this works
]


class TestUserKeyDelete:
    @pytest.mark.parametrize(
        "auth_username, auth_role, query_user, expected_status_code",
        auth_test_cases + delete_test_cases,
    )
    def test_delete_user_key_auth(
        self,
        client,
        users,
        deleted_users,
        access_token,
        make_access_token,
        auth_username,
        auth_role,
        query_user,
        expected_status_code,
    ):
        if query_user == "existing3":
            username = users[3]["username"]
        elif query_user == "existing4":
            username = users[4]["username"]
        elif query_user == "deleted":
            username = deleted_users[0]["username"]
        else:
            username = "i_dont_exists"
        if auth_username == "self":
            auth_username = username
        url = f"/users/{username}/keys"
        document = {
            "name": "one-more-key",
            "key": public_key_rsa_2048,
        }
        client.post(
            url,
            json=document,
            headers={"Authorization": access_token},
        )

        url = f"/users/{username}/keys/{fingerprint_rsa_2048}"
        if auth_username and auth_role:
            response = client.delete(
                url,
                headers={"Authorization": make_access_token(auth_username, auth_role)},
            )
        else:
            response = client.delete(url)
        assert response.status_code == expected_status_code
