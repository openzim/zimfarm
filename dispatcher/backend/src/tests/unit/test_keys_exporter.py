import pytest

from migrate_data_mongo_to_pg import KeysExporter


class TestKeysExporters:
    @pytest.mark.parametrize(
        "obj, expected_keys",
        [
            ("", set()),
            ("asd", set()),
            (1, set()),
            ([], set()),
            ([1, 2], set()),
            ({}, set()),
            ({"abc": 1}, set(["abc"])),
            ({"abc": 1, "bcd": 12}, set(["abc", "bcd"])),
            ({"abc": 1, "bcd": {"ab": 12}}, set(["abc", "bcd", "bcd.ab"])),
            (
                {"abc": 1, "bcd": {"ab": {"plk": 12}}},
                set(["abc", "bcd", "bcd.ab", "bcd.ab.plk"]),
            ),
            (
                {"abc": 1, "bcd": {"ab": {"plk": 12, "ppw": 12}}},
                set(["abc", "bcd", "bcd.ab", "bcd.ab.plk", "bcd.ab.ppw"]),
            ),
            (
                {"abc": 1, "bcd": {"ab": {"plk": 12, "ppw": 12}, "ooo": 1}},
                set(["abc", "bcd", "bcd.ab", "bcd.ab.plk", "bcd.ab.ppw", "bcd.ooo"]),
            ),
            (
                {"abc": 1, "bc": []},
                set(["abc", "bc"]),
            ),
            (
                {"abc": 1, "bc": [12]},
                set(["abc", "bc"]),
            ),
            (
                {"abc": 1, "bc": [12, {"ab": 1}]},
                set(["abc", "bc", "bc.*.ab"]),
            ),
            (
                {
                    "abc": 1,
                    "bc": [
                        12,
                        {"ab": 1},
                        {"ab": 12},
                        {"ab": 1},
                        {"bc": 1},
                        {"ab": 1, "bd": 12},
                    ],
                },
                set(["abc", "bc", "bc.*.ab", "bc.*.bc", "bc.*.bd"]),
            ),
        ],
    )
    def test_keys_exporter(self, obj, expected_keys):
        cur_keys = KeysExporter.get_keys(obj)
        assert cur_keys == expected_keys
