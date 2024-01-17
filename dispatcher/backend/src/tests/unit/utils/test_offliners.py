import pytest

from common.enum import Offliner
from utils.offliners import command_for


@pytest.mark.parametrize(
    "offliner, flags, default_publisher, expected_result",
    [
        (
            Offliner.freecodecamp,
            {},
            None,
            ["fcc2zim", '--output="/"'],
        ),  # no default publisher
        (
            Offliner.freecodecamp,
            {},
            "openZIM",
            ["fcc2zim", '--output="/"', '--publisher="openZIM"'],
        ),  # default publisher is "openZIM"
        (
            Offliner.freecodecamp,
            {},
            "Kiwix",
            ["fcc2zim", '--output="/"', '--publisher="Kiwix"'],
        ),  # default publisher is "Kiwix"
        (
            Offliner.freecodecamp,
            {"publisher": "Kiwix"},
            "openZIM",
            ["fcc2zim", '--output="/"', '--publisher="Kiwix"'],
        ),  # publisher is already set "manually" in the configuration
        (Offliner.gutenberg, {}, None, ["gutenberg2zim"]),
        (
            Offliner.gutenberg,
            {},
            "openZIM",
            ["gutenberg2zim"],
        ),  # offliner does not support the publisher flag
    ],
)
def test_command_for(
    offliner, flags, default_publisher, expected_result, set_default_publisher
):
    set_default_publisher(default_publisher)
    command = command_for(offliner=offliner, flags=flags, mount_point="/")
    assert (
        command[0] == expected_result[0]
    )  # first item is the executable, it must match
    assert set(command[1:]) == set(
        expected_result[1:]
    )  # other flags order does not matter
    assert len(command) == len(
        expected_result
    )  # but we must not have duplicate flags, so length must match
