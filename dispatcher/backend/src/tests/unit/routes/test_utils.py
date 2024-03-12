import pytest

from routes.utils import has_dict_sub_key, remove_secrets_from_response


@pytest.mark.parametrize(
    "response, expected_response",
    [
        (
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
                "name": "normal_schedule_with_double_quotes",
                "config": {
                    "task_name": "kolibri",
                    "flags": {
                        "name": "khanacademy_en_all",
                        "optimization-cache": "********",
                    },
                    "command": [
                        "kolibri2zim",
                        '--name="khanacademy_en_all"',
                        '--optimization-cache="********"',
                    ],
                },
                "upload": None,
            },
        ),
        (
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
                "name": "normal_schedule_with_single_quotes",
                "config": {
                    "task_name": "kolibri",
                    "flags": {
                        "name": "khanacademy_en_all",
                        "optimization-cache": "********",
                    },
                    "command": [
                        "kolibri2zim",
                        '--name="khanacademy_en_all"',
                        '--optimization-cache="********"',
                    ],
                },
            },
        ),
        (
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
                "name": "normal_schedule_no_quotes",
                "config": {
                    "task_name": "kolibri",
                    "flags": {
                        "name": "khanacademy_en_all",
                        "optimization-cache": "********",
                    },
                    "command": [
                        "kolibri2zim",
                        '--name="khanacademy_en_all"',
                        '--optimization-cache="********"',
                    ],
                },
            },
        ),
        (
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
                "name": "schedule_with_command_with_missing_flag",
                "config": {
                    "task_name": "kolibri",
                    "flags": {
                        "name": "khanacademy_en_all",
                        "optimization-cache": "********",
                        "flag_missing_in_commang": "some_value",
                    },
                    "command": [
                        "kolibri2zim",
                        '--name="khanacademy_en_all"',
                        '--optimization-cache="********"',
                    ],
                },
            },
        ),
        (
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
                "name": "schedule_without_command",
                "config": {
                    "task_name": "kolibri",
                    "flags": {
                        "name": "khanacademy_en_all",
                        "optimization-cache": "********",
                        "flag_missing_in_commang": "some_value",
                    },
                },
            },
        ),
        (
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
                "name": "task_with_command_and_container",
                "config": {
                    "task_name": "kolibri",
                    "flags": {
                        "name": "khanacademy_en_all",
                        "optimization-cache": "********",
                    },
                    "command": [
                        "kolibri2zim",
                        '--name="khanacademy_en_all"',
                        '--optimization-cache="********"',
                    ],
                    "str_command": (
                        'kolibri2zim --name="khanacademy_en_all" '
                        '--optimization-cache="********"'
                    ),
                },
                "container": {
                    "command": [
                        "kolibri2zim",
                        '--name="khanacademy_en_all"',
                        '--optimization-cache="********"',
                    ],
                },
            },
        ),
        (
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
                "name": "task_with_container_double_quotes",
                "config": {
                    "task_name": "kolibri",
                    "flags": {
                        "name": "khanacademy_en_all",
                        "optimization-cache": "********",
                    },
                },
                "container": {
                    "command": [
                        "kolibri2zim",
                        '--name="khanacademy_en_all"',
                        '--optimization-cache="********"',
                    ],
                },
            },
        ),
        (
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
                "name": "task_with_container_single_quotes",
                "config": {
                    "task_name": "kolibri",
                    "flags": {
                        "name": "khanacademy_en_all",
                        "optimization-cache": "********",
                    },
                },
                "container": {
                    "command": [
                        "kolibri2zim",
                        '--name="khanacademy_en_all"',
                        '--optimization-cache="********"',
                    ],
                },
            },
        ),
        (
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
                "name": "task_with_container_no_quotes",
                "config": {
                    "task_name": "kolibri",
                    "flags": {
                        "name": "khanacademy_en_all",
                        "optimization-cache": "********",
                    },
                },
                "container": {
                    "command": [
                        "kolibri2zim",
                        '--name="khanacademy_en_all"',
                        '--optimization-cache="********"',
                    ],
                },
            },
        ),
        (
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
                "name": "task_with_command_and_container_with_additional_param",
                "config": {
                    "task_name": "kolibri",
                    "flags": {
                        "name": "khanacademy_en_all",
                        "optimization-cache": "********",
                    },
                    "command": [
                        "kolibri2zim",
                        '--name="khanacademy_en_all"',
                        '--optimization-cache="********"',
                    ],
                    "str_command": (
                        'kolibri2zim --name="khanacademy_en_all" '
                        '--optimization-cache="********"'
                    ),
                },
                "container": {
                    "command": [
                        "something",
                        "kolibri2zim",
                        '--name="khanacademy_en_all"',
                        '--optimization-cache="********"',
                    ],
                },
            },
        ),
        (
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
                "name": "task_with_upload_logs",
                "config": {
                    "task_name": "kolibri",
                    "flags": {
                        "name": "khanacademy_en_all",
                        "optimization-cache": "********",
                    },
                    "command": [
                        "kolibri2zim",
                        '--name="khanacademy_en_all"',
                        '--optimization-cache="********"',
                    ],
                    "str_command": (
                        'kolibri2zim --name="khanacademy_en_all" '
                        '--optimization-cache="********"'
                    ),
                },
                "upload": {
                    "logs": {
                        "expiration": 60,
                        "upload_uri": (
                            "s3://s3.us-west-1.wasabisys.com/"
                            "?keyId=********"
                            "&secretAccessKey=********"
                            "&bucketName=org-kiwix-zimfarm-logs"
                        ),
                    },
                    "artifacts": {
                        "expiration": 20,
                        "upload_uri": (
                            "s3://s3.us-west-1.wasabisys.com/"
                            "?keyId=********"
                            "&secretAccessKey=********"
                            "&bucketName=org-kiwix-zimfarm-artifacts"
                        ),
                    },
                },
            },
        ),
        (
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
                            "something\nwhat s3://s3.us-west-1.wasabisys.com/"
                            "?keyId=this_is_super_secret"
                            "&secretAccessKey=this_is_a_super_secret"
                            "&bucketName=org-kiwix-zimfarm-logs what\n"
                            "something\n"
                        ),
                    },
                },
            },
            {
                "config": {
                    "task_name": "kolibri",
                    "flags": {
                        "name": "khanacademy_en_all",
                        "optimization-cache": "********",
                    },
                },
                "i_am_not_a_real": {
                    "response_but": {
                        "please_clean_me": (
                            "something\nwhat s3://s3.us-west-1.wasabisys.com/"
                            "?keyId=********"
                            "&secretAccessKey=********"
                            "&bucketName=org-kiwix-zimfarm-logs what\n"
                            "something\n"
                        ),
                    },
                },
            },
        ),
    ],
)
def test_remove_secrets(response, expected_response):
    remove_secrets_from_response(response)
    assert r"""'name': 'khanacademy_en_all'""" in str(response)
    assert "this_is_super_secret" not in str(response)
    if expected_response:
        assert response == expected_response


@pytest.mark.parametrize(
    "response_before,response_after",
    [
        (
            {
                "please_clean_me1": (
                    "s3://s3.us-west-1.wasabisys.com/"
                    "?keyId=this_is_super_secret"
                    "&secretAccessKey=this_is_super_secret"
                    "&bucketName=org-kiwix-zimfarm-logs"
                ),
                "please_clean_me2": (
                    "s3://s3.us-west-1.wasabisys.com/"
                    "?bucketName=org-kiwix-zimfarm-logs"
                    "&keyId=this_is_super_secret"
                    "&secretAccessKey=this_is_super_secret"
                ),
                "please_clean_me3": (
                    "s3://s3.us-west-1.wasabisys.com/"
                    "?bucketName=org-kiwix-zimfarm-logs"
                    "&keyId=this_is_super_secret"
                    "&secretAccessKey=this_is_super_secret"
                    "&something=somevalue"
                ),
                "please_clean_me4": (
                    "s3://s3.us-west-1.wasabisys.com/"
                    "?bucketName=org-kiwix-zimfarm-logs"
                    "&secretAccessKey=this_is_super_secret"
                    "&something=somevalue"
                    "&keyId=this_is_super_secret"
                    "&something2=somevalue2"
                ),
                "please_clean_me5": (
                    " s3://s3.us-west-1.wasabisys.com/"
                    "?keyId=this_is_super_secret"
                    "&secretAccessKey=this_is_super_secret"
                    "&bucketName=org-kiwix-zimfarm-logs"
                ),
                "please_clean_me6": (
                    "s3://s3.us-west-1.wasabisys.com/"
                    "?keyId=this_is_super_secret"
                    "&secretAccessKey=this_is_super_secret"
                    "&bucketName=org-kiwix-zimfarm-logs "
                ),
                "please_clean_me7": (
                    "something s3://s3.us-west-1.wasabisys.com/"
                    "?keyId=this_is_super_secret"
                    "&secretAccessKey=this_is_super_secret"
                    "&bucketName=org-kiwix-zimfarm-logs \n"
                    "something s3://s3.us-west-1.wasabisys.com/"
                    "?secretAccessKey=this_is_super_secret"
                    "&bucketName=org-kiwix-zimfarm-logs \n"
                    "something s3://s3.us-west-1.wasabisys.com/"
                    "?keyId=this_is_super_secret"
                    "&bucketName=org-kiwix-zimfarm-logs \n"
                    "something s3://s3.us-west-1.wasabisys.com/"
                    "?bucketName=org-kiwix-zimfarm-logs"
                    "&keyId=this_is_super_secret \n"
                    "something"
                ),
                "please_clean_me8": (
                    " ftp://username:password@hostname:123/path not encoded?"
                    "param=val%26ue#anchor "
                ),
            },
            {
                "please_clean_me1": (
                    "s3://s3.us-west-1.wasabisys.com/"
                    "?keyId=********"
                    "&secretAccessKey=********"
                    "&bucketName=org-kiwix-zimfarm-logs"
                ),
                "please_clean_me2": (
                    "s3://s3.us-west-1.wasabisys.com/"
                    "?bucketName=org-kiwix-zimfarm-logs"
                    "&keyId=********"
                    "&secretAccessKey=********"
                ),
                "please_clean_me3": (
                    "s3://s3.us-west-1.wasabisys.com/"
                    "?bucketName=org-kiwix-zimfarm-logs"
                    "&keyId=********"
                    "&secretAccessKey=********"
                    "&something=somevalue"
                ),
                "please_clean_me4": (
                    "s3://s3.us-west-1.wasabisys.com/"
                    "?bucketName=org-kiwix-zimfarm-logs"
                    "&secretAccessKey=********"
                    "&something=somevalue"
                    "&keyId=********"
                    "&something2=somevalue2"
                ),
                "please_clean_me5": (
                    " s3://s3.us-west-1.wasabisys.com/"
                    "?keyId=********"
                    "&secretAccessKey=********"
                    "&bucketName=org-kiwix-zimfarm-logs"
                ),
                "please_clean_me6": (
                    "s3://s3.us-west-1.wasabisys.com/"
                    "?keyId=********"
                    "&secretAccessKey=********"
                    "&bucketName=org-kiwix-zimfarm-logs "
                ),
                "please_clean_me7": (
                    "something s3://s3.us-west-1.wasabisys.com/"
                    "?keyId=********"
                    "&secretAccessKey=********"
                    "&bucketName=org-kiwix-zimfarm-logs \n"
                    "something s3://s3.us-west-1.wasabisys.com/"
                    "?secretAccessKey=********"
                    "&bucketName=org-kiwix-zimfarm-logs \n"
                    "something s3://s3.us-west-1.wasabisys.com/"
                    "?keyId=********"
                    "&bucketName=org-kiwix-zimfarm-logs \n"
                    "something s3://s3.us-west-1.wasabisys.com/"
                    "?bucketName=org-kiwix-zimfarm-logs"
                    "&keyId=******** \n"
                    "something"
                ),
                "please_clean_me8": (
                    " ftp://username:--------@hostname:123/path not encoded?param="
                    "val%26ue#anchor "
                ),
            },
        ),
    ],
)
def test_remove_secrets_url_kept(response_before, response_after):
    remove_secrets_from_response(response_before)
    assert response_before == response_after


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
