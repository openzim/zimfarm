import pytest

from routes.utils import has_dict_sub_key, remove_secrets_from_response


@pytest.mark.parametrize(
    "response",
    [
        {
            "name": "normal_schedule_with_double_quotes",
            "config": {
                "task_name": "kolibri",
                "flags": {
                    "name": "khanacademy_en_all",
                    "optimization-cache": "this_is_super_secret",
                },
                "command": [
                    "kolibri2zim",
                    '--name="khanacademy_en_all"',
                    '--optimization-cache="this_is_super_secret"',
                ],
            },
            "upload": None,
        },
        {
            "name": "normal_schedule_with_single_quotes",
            "config": {
                "task_name": "kolibri",
                "flags": {
                    "name": "khanacademy_en_all",
                    "optimization-cache": "this_is_super_secret",
                },
                "command": [
                    "kolibri2zim",
                    '--name="khanacademy_en_all"',
                    "--optimization-cache='this_is_super_secret'",
                ],
            },
        },
        {
            "name": "normal_schedule_no_quotes",
            "config": {
                "task_name": "kolibri",
                "flags": {
                    "name": "khanacademy_en_all",
                    "optimization-cache": "this_is_super_secret",
                },
                "command": [
                    "kolibri2zim",
                    '--name="khanacademy_en_all"',
                    "--optimization-cache=this_is_super_secret",
                ],
            },
        },
        {
            "name": "schedule_with_command_with_missing_flag",
            "config": {
                "task_name": "kolibri",
                "flags": {
                    "name": "khanacademy_en_all",
                    "optimization-cache": "this_is_super_secret",
                    "flag_missing_in_commang": "some_value",
                },
                "command": [
                    "kolibri2zim",
                    '--name="khanacademy_en_all"',
                    '--optimization-cache="this_is_super_secret"',
                ],
            },
        },
        {
            "name": "schedule_without_command",
            "config": {
                "task_name": "kolibri",
                "flags": {
                    "name": "khanacademy_en_all",
                    "optimization-cache": "this_is_super_secret",
                    "flag_missing_in_commang": "some_value",
                },
            },
        },
        {
            "name": "task_with_command_and_container",
            "config": {
                "task_name": "kolibri",
                "flags": {
                    "name": "khanacademy_en_all",
                    "optimization-cache": "this_is_super_secret",
                },
                "command": [
                    "kolibri2zim",
                    '--name="khanacademy_en_all"',
                    '--optimization-cache="this_is_super_secret"',
                ],
                "str_command": (
                    'kolibri2zim --name="khanacademy_en_all" '
                    '--optimization-cache="this_is_super_secret"'
                ),
            },
            "container": {
                "command": [
                    "kolibri2zim",
                    '--name="khanacademy_en_all"',
                    '--optimization-cache="this_is_super_secret"',
                ],
            },
        },
        {
            "name": "task_with_container_double_quotes",
            "config": {
                "task_name": "kolibri",
                "flags": {
                    "name": "khanacademy_en_all",
                    "optimization-cache": "this_is_super_secret",
                },
            },
            "container": {
                "command": [
                    "kolibri2zim",
                    '--name="khanacademy_en_all"',
                    '--optimization-cache="this_is_super_secret"',
                ],
            },
        },
        {
            "name": "task_with_container_single_quotes",
            "config": {
                "task_name": "kolibri",
                "flags": {
                    "name": "khanacademy_en_all",
                    "optimization-cache": "this_is_super_secret",
                },
            },
            "container": {
                "command": [
                    "kolibri2zim",
                    '--name="khanacademy_en_all"',
                    "--optimization-cache='this_is_super_secret'",
                ],
            },
        },
        {
            "name": "task_with_container_no_quotes",
            "config": {
                "task_name": "kolibri",
                "flags": {
                    "name": "khanacademy_en_all",
                    "optimization-cache": "this_is_super_secret",
                },
            },
            "container": {
                "command": [
                    "kolibri2zim",
                    '--name="khanacademy_en_all"',
                    "--optimization-cache=this_is_super_secret",
                ],
            },
        },
        {
            "name": "task_with_command_and_container_with_additional_param",
            "config": {
                "task_name": "kolibri",
                "flags": {
                    "name": "khanacademy_en_all",
                    "optimization-cache": "this_is_super_secret",
                },
                "command": [
                    "kolibri2zim",
                    '--name="khanacademy_en_all"',
                    '--optimization-cache="this_is_super_secret"',
                ],
                "str_command": (
                    'kolibri2zim --name="khanacademy_en_all" '
                    '--optimization-cache="this_is_super_secret"'
                ),
            },
            "container": {
                "command": [
                    "something",
                    "kolibri2zim",
                    '--name="khanacademy_en_all"',
                    '--optimization-cache="this_is_super_secret"',
                ],
            },
        },
        {
            "name": "task_with_upload_logs",
            "config": {
                "task_name": "kolibri",
                "flags": {
                    "name": "khanacademy_en_all",
                    "optimization-cache": "this_is_super_secret",
                },
                "command": [
                    "kolibri2zim",
                    '--name="khanacademy_en_all"',
                    '--optimization-cache="this_is_super_secret"',
                ],
                "str_command": (
                    'kolibri2zim --name="khanacademy_en_all" '
                    '--optimization-cache="this_is_super_secret"'
                ),
            },
            "upload": {
                "logs": {
                    "expiration": 60,
                    "upload_uri": (
                        "s3://s3.us-west-1.wasabisys.com/"
                        "?keyId=this_is_super_secret"
                        "&secretAccessKey=this_is_super_secret"
                        "&bucketName=org-kiwix-zimfarm-logs"
                    ),
                },
                "artifacts": {
                    "expiration": 20,
                    "upload_uri": (
                        "s3://s3.us-west-1.wasabisys.com/"
                        "?keyId=this_is_super_secret"
                        "&secretAccessKey=this_is_super_secret"
                        "&bucketName=org-kiwix-zimfarm-artifacts"
                    ),
                },
            },
        },
        {
            "config": {
                "task_name": "kolibri",
                "flags": {
                    "name": "khanacademy_en_all",
                    "optimization-cache": "this_is_super_secret",
                },
            },
            "i_am_not_a_real": {
                "response_but": {
                    "please_clean_me": (
                        "s3://s3.us-west-1.wasabisys.com/"
                        "?keyId=this_is_super_secret"
                        "&secretAccessKey=this_is_super_secret"
                        "&bucketName=org-kiwix-zimfarm-logs"
                    ),
                },
            },
        },
    ],
)
def test_remove_secrets(response):
    remove_secrets_from_response(response)
    assert r"""'name': 'khanacademy_en_all'""" in str(response)
    assert "this_is_super_secret" not in str(response)


@pytest.mark.parametrize(
    "data, keys, has",
    [
        (
            {
                "config": {
                    "task_name": "kolibri",
                },
                "upload": None,
            },
            ["config", "task_name"],
            True,
        ),
        (
            {
                "config": {
                    "task_name": "kolibri",
                },
                "upload": None,
            },
            ["config", "something"],
            False,
        ),
        (
            {
                "config": {
                    "task_name": "kolibri",
                    "flags": {
                        "name": "khanacademy_en_all",
                    },
                },
                "upload": None,
            },
            ["config", "flags"],
            True,
        ),
        (
            {
                "config": {
                    "task_name": "kolibri",
                    "flags": {
                        "name": "khanacademy_en_all",
                    },
                },
                "upload": None,
            },
            ["config", "flags", "name"],
            True,
        ),
        (
            {
                "config": {
                    "task_name": "kolibri",
                    "flags": {
                        "name": "khanacademy_en_all",
                    },
                },
                "upload": None,
            },
            ["config", "flags", "language"],
            False,
        ),
        (
            {
                "config": {"task_name": "kolibri", "flags": None},
                "upload": None,
            },
            ["config", "flags", "name"],
            False,
        ),
        (
            {
                "config": {"task_name": "kolibri", "flags": None},
                "upload": None,
            },
            ["upload", "command"],
            False,
        ),
    ],
)
def test_has_dict_sub_key(data, keys, has):
    assert has == has_dict_sub_key(data, keys)
