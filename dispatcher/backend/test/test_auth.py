import pytest
import requests


@pytest.mark.usefixtures('root', 'authorize', 'access_token', 'refresh_token')
class TestAuthorize:
    def test_password_auth(self, authorize):
        assert 'access_token' in authorize
        assert 'refresh_token' in authorize

    def test_access_token_validation(self, root, access_token):
        response = requests.post(
            url=root + "/auth/validate",
            headers={"access-token": access_token},
        )
        assert response.status_code == 200

    def test_refresh_token(self, root, refresh_token):
        # test refresh token
        response = requests.post(
            url=root + "/auth/token",
            headers={"refresh-token": refresh_token},
        )

        # refresh success
        refresh_json = response.json()
        assert response.status_code == 200
        assert 'access_token' in refresh_json
        assert 'refresh_token' in refresh_json

        new_access_token = refresh_json['access_token']
        new_refresh_token = refresh_json['refresh_token']

        # test new access token
        response = requests.post(
            url=root + "/auth/validate",
            headers={"access-token": new_access_token},
        )
        assert response.status_code == 200

        # test old refresh token no longer works
        response = requests.post(
            url=root + "/auth/token",
            headers={"refresh-token": refresh_token},
        )
        assert response.status_code == 401

        # test new refresh token works
        response = requests.post(
            url=root + "/auth/token",
            headers={"refresh-token": new_refresh_token},
        )
        assert response.status_code == 200
