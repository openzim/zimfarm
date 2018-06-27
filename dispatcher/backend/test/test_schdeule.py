import requests
import pytest


@pytest.mark.usefixtures('root', 'access_token')
class TestAuthorize:
    def test_get_schedule(self, root, access_token):
        response = requests.get(
            url=root + "/schedules/",
            headers={"token": access_token},
        )

        response_json = response.json()
        assert response is not None

        items = response_json.get('items', None)
        assert isinstance(items, list)

        meta = response_json.get('meta', {})
        limit = meta.get('limit', None)
        skip = meta.get('skip', None)
        assert isinstance(limit, int)
        assert isinstance(skip, int)

        assert len(items) == limit
        for item in items:
            assert '_id' in item
