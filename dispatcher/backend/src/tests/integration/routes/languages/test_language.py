import pytest


@pytest.fixture()
def language(make_language):
    return make_language(code="fr", name_en="French", name_native="Français")


class TestLanguagesList:
    def test_list_languages_no_param(self, client, access_token, languages):
        """Test list languages"""

        url = '/api/languages/'
        response = client.get(url, headers={'Authorization': access_token})
        assert response.status_code == 200

        response_json = response.get_json()
        assert 'items' in response_json
        assert len(response_json['items']) == 27
        for item in response_json['items']:
            assert isinstance(item['_id'], str)
            assert isinstance(item['code'], str)
            assert isinstance(item['name_en'], str)
            assert isinstance(item['name_native'], str)

    @pytest.mark.parametrize('skip, limit, expected', [
        (0, 10, 10), (5, 10, 10), (20, 10, 7),
        (0, 100, 27), ('', 10, 10), (5, 'abc', 22)
    ])
    def test_list_languages_with_param(self, client, access_token, languages, skip, limit, expected):
        """Test list languages"""

        url = '/api/languages/?skip={}&limit={}'.format(skip, limit)
        response = client.get(url, headers={'Authorization': access_token})
        assert response.status_code == 200

        response_json = response.get_json()
        assert 'items' in response_json
        assert len(response_json['items']) == expected

    def test_unauthorized(self, client):
        url = '/api/languages/'
        response = client.get(url)
        assert response.status_code == 401
        assert response.get_json() == {'error': 'token invalid'}


class TestLanguageGet:
    def test_get_language_with_id(self, client, access_token, language):
        """Test get language with id"""

        url = '/api/languages/{}'.format(language['_id'])
        response = client.get(url, headers={'Authorization': access_token})
        assert response.status_code == 200

        language['_id'] = str(language['_id'])
        assert response.get_json() == language

    def test_get_language_with_code(self, client, access_token, language):
        """Test get language with code"""

        url = '/api/languages/{}'.format(language['code'])
        response = client.get(url, headers={'Authorization': access_token})
        assert response.status_code == 200

        language['_id'] = str(language['_id'])
        assert response.get_json() == language

    @pytest.mark.parametrize('code, expected_en, expected_native', [
        ("fr", "French", "Français"),
        ("ady", "Adyghe", "адыгабзэ"),
        ("ar", "Arabic", "العربية")
    ])
    def test_get_language_in_fixtures(self, client, access_token, languages, code, expected_en, expected_native):
        """Test get language with code"""

        url = '/api/languages/{}'.format(code)
        response = client.get(url, headers={'Authorization': access_token})
        assert response.status_code == 200

        data = response.get_json()
        assert data['name_en'] == expected_en
        assert data['name_native'] == expected_native

    @pytest.mark.parametrize('code', ['it', 'bm', 'ses'])
    def test_missing(self, client, access_token, languages, code):
        """Test get language with code"""

        url = '/api/languages/{}'.format(code)
        response = client.get(url, headers={'Authorization': access_token})
        assert response.status_code == 404

    def test_unauthorized(self, client, access_token, language):
        url = '/api/languages/{}'.format(language['code'])
        response = client.get(url)
        assert response.status_code == 401
        assert response.get_json() == {'error': 'token invalid'}


class TestlanguagePost:

    def test_create_language(self, client, access_token):
        """Test delete language with id or code"""

        language = {"code": "wo", "name_en": "Wolof", "name_native": "wolof"}

        url = '/api/languages/'
        response = client.post(url, json=language, headers={'Authorization': access_token})
        assert response.status_code == 201

        url = '/api/languages/{}'.format(language['code'])
        response = client.get(url, headers={'Authorization': access_token})
        assert response.status_code == 200

        response_json = response.get_json()
        language['_id'] = response_json['_id']
        assert response.get_json() == language

    def test_unauthorized(self, client, access_token):
        language = {"code": "wo", "name_en": "Wolof", "name_native": "wolof"}
        url = '/api/languages/'
        response = client.post(url, json=language)
        assert response.status_code == 401
        assert response.get_json() == {'error': 'token invalid'}


class TestlanguagePatch:

    def test_patch_language(self, client, access_token):
        """Test delete language with id or code"""

        language = {"name_en": "Wolof", "name_native": "wolofo"}

        url = '/api/languages/wo'
        response = client.patch(url, json=language, headers={'Authorization': access_token})
        assert response.status_code == 204

        response = client.get(url, headers={'Authorization': access_token})
        assert response.status_code == 200

        assert response.get_json()['name_native'] == language['name_native']

    def test_unauthorized(self, client, access_token):
        language = {"name_en": "Wolof", "name_native": "wolofo"}
        url = '/api/languages/wo'
        response = client.patch(url, json=language)
        assert response.status_code == 401
        assert response.get_json() == {'error': 'token invalid'}


class TestlanguageDelete:
    @pytest.mark.parametrize('key', ['_id', 'code'])
    def test_delete_language(self, client, access_token, language, key):
        """Test delete language with id or code"""

        url = '/api/languages/{}'.format(language[key])
        response = client.delete(url, headers={'Authorization': access_token})
        assert response.status_code == 204

    def test_delete_posted(self, client, access_token):
        """Test delete language with id or code"""

        url = '/api/languages/wo'
        response = client.delete(url, headers={'Authorization': access_token})
        assert response.status_code == 204

    def test_unauthorized(self, client, access_token, language):
        url = '/api/languages/{}'.format(language['code'])
        response = client.delete(url)
        assert response.status_code == 401
        assert response.get_json() == {'error': 'token invalid'}
