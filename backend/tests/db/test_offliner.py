from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.common.schemas.orms import OfflinerSchema
from zimfarm_backend.db.exceptions import (
    RecordAlreadyExistsError,
    RecordDoesNotExistError,
)
from zimfarm_backend.db.offliner import (
    _cache_map,  # pyright: ignore[reportPrivateUsage]
    create_offliner,
    get_all_offliners,
    get_offliner,
    get_offliner_by_id_or_none,
)


def test_get_offliner_missing(dbsession: OrmSession):
    with pytest.raises(RecordDoesNotExistError):
        get_offliner(dbsession, "invalid")


def test_get_offliner_by_id_or_none_missing(dbsession: OrmSession):
    offliner = get_offliner_by_id_or_none(dbsession, "invalid")
    assert offliner is None


def test_get_offliner_by_id_or_none_exists(
    dbsession: OrmSession, ted_offliner: OfflinerSchema
):
    offliner = get_offliner_by_id_or_none(dbsession, ted_offliner.id)
    assert offliner is not None
    assert offliner.id == ted_offliner.id


def test_get_offliner_exists(dbsession: OrmSession, ted_offliner: OfflinerSchema):
    offliner = get_offliner(dbsession, ted_offliner.id)
    assert offliner.id == ted_offliner.id


def test_create_offliner(dbsession: OrmSession):
    create_offliner(
        dbsession,
        "ted",
        "DashModel",
        "openzim/ted",
        "ted2zim",
    )
    offliner = get_offliner(dbsession, "ted")
    assert offliner.id == "ted"
    assert offliner.base_model == "DashModel"
    assert offliner.docker_image_name == "openzim/ted"
    assert offliner.command_name == "ted2zim"


def test_create_duplicate_offliner(dbsession: OrmSession, ted_offliner: OfflinerSchema):
    with pytest.raises(RecordAlreadyExistsError):
        create_offliner(
            dbsession,
            ted_offliner.id,
            ted_offliner.base_model,
            ted_offliner.docker_image_name,
            ted_offliner.command_name,
        )


class TestOfflinerCache:
    def setup_method(self):
        _cache_map.clear()

    def teardown_method(self):
        _cache_map.clear()

    def test_get_offliner_cache_miss(
        self, dbsession: OrmSession, ted_offliner: OfflinerSchema
    ):
        """Test that get_offliner populates cache on first call (cache miss)."""
        # Ensure cache is empty
        assert ted_offliner.id not in _cache_map

        # First call should hit database and populate cache
        with patch(
            "zimfarm_backend.db.offliner.get_offliner_by_id_or_none"
        ) as mock_get_by_id:
            mock_get_by_id.return_value = ted_offliner
            result = get_offliner(dbsession, ted_offliner.id)

            mock_get_by_id.assert_called_once_with(dbsession, ted_offliner.id)
            assert result.id == ted_offliner.id
            assert ted_offliner.id in _cache_map
            assert _cache_map[ted_offliner.id] == ted_offliner

    def test_get_offliner_cache_hit(
        self, dbsession: OrmSession, ted_offliner: OfflinerSchema
    ):
        """Test that get_offliner uses cache on subsequent calls (cache hit)."""
        # Pre-populate cache
        _cache_map[ted_offliner.id] = ted_offliner

        # Call should use cache, not database
        with patch(
            "zimfarm_backend.db.offliner.get_offliner_by_id_or_none"
        ) as mock_get_by_id:
            result = get_offliner(dbsession, ted_offliner.id)

            mock_get_by_id.assert_not_called()
            assert result.id == ted_offliner.id
            assert result == ted_offliner

    def test_get_all_offliners_populates_cache(
        self, dbsession: OrmSession, ted_offliner: OfflinerSchema
    ):
        """Test that get_all_offliners populates the cache."""
        # Ensure cache is empty
        assert ted_offliner.id not in _cache_map

        # Call get_all_offliners
        with patch("zimfarm_backend.db.offliner.Session.scalars") as mock_scalars:
            # Mock the database query to return our test offliner
            mock_offliner = type(
                "MockOffliner",
                (),
                {
                    "id": ted_offliner.id,
                    "base_model": ted_offliner.base_model,
                    "docker_image_name": ted_offliner.docker_image_name,
                    "command_name": ted_offliner.command_name,
                    "ci_secret_hash": ted_offliner.ci_secret_hash,
                },
            )()
            mock_scalars.return_value.all.return_value = [mock_offliner]

            result = get_all_offliners(dbsession)

            assert len(result) == 1
            assert result[0].id == ted_offliner.id
            assert ted_offliner.id in _cache_map
            assert _cache_map[ted_offliner.id].id == ted_offliner.id

    def test_get_offliner_missing_not_cached(self, dbsession: OrmSession):
        """Test that missing offliners are not cached."""
        assert len(_cache_map) == 0

        with pytest.raises(RecordDoesNotExistError):
            get_offliner(dbsession, "non_existent")

        assert len(_cache_map) == 0
