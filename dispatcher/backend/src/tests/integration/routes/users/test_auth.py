import base64
import datetime
import os
import pathlib
import subprocess
import tempfile

import pytest

OPENSSL_BIN = os.getenv("OPENSSL_BIN", "openssl")


class TestAuthentication:
    def do_test_token(self, client, token):
        headers = {"Authorization": token, "Content-Type": "application/json"}
        response = client.get("/auth/test", headers=headers)
        assert response.status_code == 204

    def do_get_token_with(self, client, username, password):
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        response = client.post(
            "/auth/authorize",
            headers=headers,
            data=f"username={username}&password={password}",
        )
        return response

    @pytest.mark.parametrize(
        "username, password, assert_code",
        [
            ("some-user", "hop", 401),
            ("some-user2", "some-password", 401),
            ("some-user", "some-password", 200),
            ("del_user_0", "some-password", 401),
        ],
    )
    def test_credentials(self, client, user, username, password, assert_code):
        response = self.do_get_token_with(client, username, password)
        assert response.status_code == assert_code
        if assert_code == 200:
            response_json = response.get_json()
            assert "access_token" in response_json

            self.do_test_token(client, response_json["access_token"])

    def test_oauth2_refresh_token_ok(self, client, user):
        response = self.do_get_token_with(client, "some-user", "some-password")
        assert response.status_code == 200
        response_json = response.get_json()
        access_token = response_json["access_token"]
        refresh_token = response_json["refresh_token"]

        headers = {
            "Authorization": access_token,
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {"refresh_token": refresh_token, "grant_type": "refresh_token"}
        response = client.post("/auth/oauth2", headers=headers, data=data)
        assert response.status_code == 200
        response = client.post("/auth/oauth2", headers=headers, data=data)
        assert response.status_code == 401

    def test_oauth2_refresh_token_deleted_user(self, client, make_user, access_token):
        admin_access_token = access_token
        username = "847765870620"
        make_user(username=username)
        response = self.do_get_token_with(client, username, "some-password")
        assert response.status_code == 200
        response_json = response.get_json()
        access_token = response_json["access_token"]
        refresh_token = response_json["refresh_token"]

        response = client.delete(
            f"/users/{username}", headers={"Authorization": admin_access_token}
        )
        assert response.status_code == 204

        headers = {
            "Authorization": access_token,
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {"refresh_token": refresh_token, "grant_type": "refresh_token"}
        response = client.post("/auth/oauth2", headers=headers, data=data)
        assert response.status_code == 401

    def test_refresh_token_ok(self, client, user):
        response = self.do_get_token_with(client, "some-user", "some-password")
        assert response.status_code == 200
        response_json = response.get_json()
        access_token = response_json["access_token"]
        refresh_token = response_json["refresh_token"]

        headers = {
            "Authorization": access_token,
            "Content-Type": "application/json",
            "refresh-token": refresh_token,
        }

        assert client.post("/auth/token", headers=headers).status_code == 200
        assert client.post("/auth/token", headers=headers).status_code == 401

    def test_refresh_token_deleted_user(self, client, make_user, access_token):
        admin_access_token = access_token
        username = "80aae2dc294b"
        make_user(username=username)
        response = self.do_get_token_with(client, username, "some-password")
        assert response.status_code == 200
        response_json = response.get_json()
        access_token = response_json["access_token"]
        refresh_token = response_json["refresh_token"]

        response = client.delete(
            f"/users/{username}", headers={"Authorization": admin_access_token}
        )
        assert response.status_code == 204

        headers = {
            "Authorization": access_token,
            "Content-Type": "application/json",
            "refresh-token": refresh_token,
        }

        assert client.post("/auth/token", headers=headers).status_code == 401

    def test_test_auth(self, client, make_user, access_token):
        admin_access_token = access_token
        username = "b6027cb3214c"
        make_user(username=username)
        response = self.do_get_token_with(client, username, "some-password")
        assert response.status_code == 200
        response_json = response.get_json()
        access_token = response_json["access_token"]

        response = client.get("/auth/test", headers={"Authorization": access_token})
        assert response.status_code == 204

        response = client.delete(
            f"/users/{username}", headers={"Authorization": admin_access_token}
        )
        assert response.status_code == 204

        # for now, an access token is not invalidated when a user is deleted
        # its lifespan is short enough so that we don't need to do it, especially
        # since refresh_token cannot be exchanged for a new access token for a deleted
        # user ; this is done so for performance reason, because otherwise every
        # authenticated call would mean one call to the DB to check the user status
        # or we would need to cache this data in memory
        response = client.get("/auth/test", headers={"Authorization": access_token})
        assert response.status_code == 204

    @pytest.mark.parametrize(
        "username, key_to_use, assert_code",
        [
            ("some-user", "good", 200),
            ("some-user2", "good", 401),
            ("some-user", "bad", 401),
            ("some-user", "none", 401),
            ("del_user_0", "good", 401),
        ],
    )
    def test_ssh(
        self,
        client,
        user,
        deleted_users,
        working_private_key,
        not_working_private_key,
        username,
        key_to_use,
        assert_code,
    ):
        key = {"good": working_private_key, "bad": not_working_private_key}.get(
            key_to_use,
            "-----BEGIN RSA PRIVATE KEY-----\nnope\n-----END RSA PRIVATE KEY-----\n",
        )

        if key_to_use == "none":
            with pytest.raises(IOError):
                self.do_test_ssh(client, key, username)
        else:
            response = self.do_test_ssh(client, key, username)
            if response.status_code != assert_code:
                print(response.get_json())
            assert response.status_code == assert_code
            if assert_code == 200:
                self.do_test_token(client, response.get_json()["access_token"])

    def do_test_ssh(self, client, private_key, username):
        # build the SSH payload
        now = datetime.datetime.utcnow()
        message = f"{username}:{now.isoformat()}"

        tmp_dir = pathlib.Path(tempfile.mkdtemp())

        # write private key to a temp file
        private_key_path = tmp_dir.joinpath("key")
        with open(private_key_path, "wb") as fp:
            fp.write(private_key.encode("ASCII"))

        message_path = tmp_dir.joinpath("message")
        signatured_path = tmp_dir.joinpath(f"{message_path.name}.sig")
        with open(message_path, "w", encoding="ASCII") as fp:
            fp.write(message)
        pkey_util = subprocess.run(
            [
                OPENSSL_BIN,
                "pkeyutl",
                "-sign",
                "-inkey",
                str(private_key_path),
                "-in",
                str(message_path),
                "-out",
                signatured_path,
            ]
        )

        if pkey_util.returncode != 0:
            raise IOError("unable to sign authentication payload")

        with open(signatured_path, "rb") as fp:
            b64_signature = base64.b64encode(fp.read()).decode()

        headers = {
            "Content-type": "application/json",
            "X-SSHAuth-Message": message,
            "X-SSHAuth-Signature": b64_signature,
        }
        return client.post("/auth/ssh_authorize", headers=headers)
