import pytest
from marshmallow.exceptions import ValidationError

from common.schemas.models import ScheduleConfigSchema
from common.schemas.offliners import MWOfflinerFlagsSchema, PhetFlagsSchema


def make_mwoffliner_flags(**kwargs):
    flags = {
        "mwUrl": "https://www.wikipedia.org",
        "adminEmail": "contact@kiwix.org",
        "format": ["nopic", "novid"],
        "useDownloadCache": True,
        "verbose": False,
        "speed": 1.0,
        "articleList": "https://example.com",
        "customZimFavicon": "https://example.com/icon.jpeg",
        "customZimTitle": "Custom Title",
        "customZimDescription": "Custom Description",
    }
    flags.update(kwargs)
    return flags


def make_mwoffliner_config(**kwargs):
    config = {
        "task_name": "mwoffliner",
        "warehouse_path": "/wikipedia",
        "image": {"name": "openzim/mwoffliner", "tag": "1.8.0"},
        "flags": make_mwoffliner_flags(),
        "resources": {"cpu": 3, "memory": 512 * 1048576, "disk": 2 ** 30},
    }
    config.update(kwargs)
    return config


def make_phet_config(**kwargs):
    config = {
        "task_name": "phet",
        "warehouse_path": "/phet",
        "image": {"name": "openzim/phet", "tag": "latest"},
        "flags": {},
        "resources": {"cpu": 3, "memory": 512 * 1048576, "disk": 2 ** 30},
    }
    config.update(kwargs)
    return config


class TestMWOfflinerFlagsValidator:
    def test_valid(self):
        flags = {
            "mwUrl": "https://www.wikipedia.org",
            "adminEmail": "contact@kiwix.org",
        }
        MWOfflinerFlagsSchema().load(flags)

        flags = {
            "mwUrl": "https://en.wikipedia.org/",
            "adminEmail": "contact@kiwix.org",
            "articleList": "https://en.wikipedia.org/list",
            "customZimFavicon": "https://en.wikipedia.org/icon.png",
            "customZimTitle": "Wikipedia Offline",
            "customZimDescription": "An offline Wikipedia",
            "customZimTags": "Highlight",
            "customMainPage": "Main_Page",
            "filenamePrefix": "wikipedia_all",
            "format": ["nopic", "novid", "nodet,nopic"],
            "keepEmptyParagraphs": False,
            "mwWikiPath": "/wiki",
            "mwApiPath": "/w/api.php",
            "mwModulePath": "/w/load.php",
            "mwDomain": "en.wikipedia.org",
            "mwUsername": "ausername",
            "mwPassword": "apassword",
            "minifyHtml": False,
            "publisher": "Kiwix",
            "requestTimeout": 2,
            "useDownloadCache": True,
            "speed": 1.0,
            "verbose": False,
            "withoutZimFullTextIndex": False,
            "addNamespaces": "100,200",
            "getCategories": False,
            "noLocalParserFallback": True,
        }
        MWOfflinerFlagsSchema().load(flags)

        flags = make_mwoffliner_flags()
        MWOfflinerFlagsSchema().load(flags)

    @pytest.mark.parametrize("missing_key", ["mwUrl", "adminEmail"])
    def test_missing_required(self, missing_key):
        with pytest.raises(ValidationError):
            flags = make_mwoffliner_flags()
            flags.pop(missing_key)
            MWOfflinerFlagsSchema().load(flags)

    def test_extra_key(self):
        with pytest.raises(ValidationError):
            flags = make_mwoffliner_flags()
            flags["extra"] = "some_value"
            MWOfflinerFlagsSchema().load(flags)

    @pytest.mark.parametrize(
        "data",
        [
            {"mwUrl": "http:/example.com"},
            {"adminEmail": "user @example.com"},
            {"articleList": "abc"},
            {"customZimFavicon": "http:/example.com"},
            {"customZimTitle": 123},
            {"customZimDescription": None},
            {"customZimTags": False},
            {"customZimTags": ["Highlight", 123]},
            {"customMainPage": 123},
            {"filenamePrefix": 123},
            {"format": ["pic", 123]},
            {"keepEmptyParagraphs": "True"},
            {"mwWikiPath": 123},
            {"mwApiPath": 123},
            {"mwModulePath": 123},
            {"mwDomain": 123},
            {"mwUsername": 123},
            {"mwPassword": 123},
            {"minifyHtml": "False"},
            {"publisher": 123},
            {"requestTimeout": "1.23"},
            {"useCache": "False"},
            {"speed": "zero"},
            {"verbose": "False"},
            {"withoutZimFullTextIndex": "False"},
            {"addNamespaces": 123},
            {"getCategories": "False"},
            {"noLocalParserFallback": "False"},
        ],
    )
    def test_invalid_field(self, data):
        with pytest.raises(ValidationError):
            flags = make_mwoffliner_flags(**data)
            MWOfflinerFlagsSchema().load(flags)

    @pytest.mark.parametrize(
        "mwformat, expected",
        [
            (["nopic", "nopic"], ["nopic"]),
            (["novid", "novid", "novid", "nopic"], ["novid", "nopic"]),
        ],
    )
    def test_duplicated_formats(self, mwformat, expected):
        flags = make_mwoffliner_flags(format=mwformat)
        result = MWOfflinerFlagsSchema().ingest(flags)
        assert set(result["format"]) == set(expected)


class TestPhetFlagsValidator:
    def test_valid(self):
        flags = {}
        PhetFlagsSchema().load(flags)

    def test_invalid_mwoffliner(self):
        with pytest.raises(ValidationError):
            flags = make_mwoffliner_flags()
            PhetFlagsSchema().load(flags)


class TestConfigValidator:
    @pytest.mark.parametrize("make_config", [make_mwoffliner_config, make_phet_config])
    def test_valid(self, make_config):
        config = make_config()
        ScheduleConfigSchema().load(config)

    @pytest.mark.parametrize(
        "missing_key", ["task_name", "warehouse_path", "image", "flags"]
    )
    def test_missing_required(self, missing_key):
        with pytest.raises(ValidationError):
            config = make_mwoffliner_config()
            config.pop(missing_key)
            ScheduleConfigSchema().load(config)

    def test_extra_key(self):
        with pytest.raises(ValidationError):
            config = make_mwoffliner_config()
            config["extra"] = "some_value"
            ScheduleConfigSchema().load(config)

    @pytest.mark.parametrize(
        "data",
        [
            {"task_name": "unknown"},
            {"warehouse_path": "/wikipedia/subdir"},
            {"warehouse_path": "/bad_path"},
            {"image": {"name": "unknown_offliner", "tag": "1.0"}},
            {"image": {"name": "unknown_offliner"}},
            {"flags": make_mwoffliner_flags(mwUrl="bad_url")},
        ],
    )
    def test_invalid_field(self, data):
        with pytest.raises(ValidationError):
            flags = make_mwoffliner_flags(**data)
            MWOfflinerFlagsSchema().load(flags)
