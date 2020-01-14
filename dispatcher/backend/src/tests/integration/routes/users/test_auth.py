import os
import base64
import pathlib
import datetime
import tempfile
import subprocess

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
        ],
    )
    def test_credentials(self, client, user, username, password, assert_code):
        response = self.do_get_token_with(client, username, password)
        assert response.status_code == assert_code
        if assert_code == 200:
            response_json = response.get_json()
            assert "access_token" in response_json

            self.do_test_token(client, response_json["access_token"])

    def test_refresh_token(self, client, user):
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
        headers["refresh-token"] = "".join(headers["refresh-token"][:-1])
        assert client.post("/auth/token", headers=headers).status_code == 401

    @pytest.mark.parametrize(
        "username, key_to_use, assert_code",
        [
            ("some-user", "good", 200),
            ("some-user2", "good", 401),
            ("some-user", "bad", 401),
            ("some-user", "none", 401),
        ],
    )
    def test_ssh(
        self,
        client,
        user,
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
            b64_signature = base64.b64encode(fp.read())

        headers = {
            "Content-type": "application/json",
            "X-SSHAuth-Message": message,
            "X-SSHAuth-Signature": b64_signature,
        }
        return client.post("/auth/ssh_authorize", headers=headers)
