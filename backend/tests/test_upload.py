# ruff: noqa: E501
import urllib.parse
from unittest.mock import MagicMock

import pytest

from zimfarm_backend.common.constants import SECRET_STRING_LENGTH
from zimfarm_backend.common.upload import (
    build_task_upload_uris,
    rebuild_uri,
    safe_upload_uri,
    upload_url,
)


@pytest.mark.parametrize(
    "uri_string,query,expected_url",
    [
        pytest.param(
            "https://example.com/path",
            None,
            "https://example.com/path",
            id="simple-uri-no-query",
        ),
        pytest.param(
            "https://example.com/path?key=value",
            None,
            "https://example.com/path?key=value",
            id="uri-with-existing-query",
        ),
        pytest.param(
            "https://example.com/path",
            "newkey=newvalue",
            "https://example.com/path?newkey=newvalue",
            id="uri-with-new-query",
        ),
        pytest.param(
            "https://example.com/path?oldkey=oldvalue",
            "newkey=newvalue",
            "https://example.com/path?newkey=newvalue",
            id="uri-replacing-query",
        ),
        pytest.param(
            "https://user:pass@example.com/path",
            None,
            "https://user:pass@example.com/path",
            id="uri-with-credentials",
        ),
        pytest.param(
            "https://user@example.com/path",
            None,
            "https://user@example.com/path",
            id="uri-with-username-only",
        ),
        pytest.param(
            "https://example.com:8080/path",
            None,
            "https://example.com:8080/path",
            id="uri-with-port",
        ),
        pytest.param(
            "https://user:pass@example.com:8080/path?key=value",
            "newkey=newvalue",
            "https://user:pass@example.com:8080/path?newkey=newvalue",
            id="uri-with-all-components",
        ),
        pytest.param(
            "s3://bucket/path",
            None,
            "s3://bucket/path",
            id="s3-uri",
        ),
        pytest.param(
            "sftp://user@host/path",
            None,
            "sftp://user@host/path",
            id="sftp-uri",
        ),
    ],
)
def test_rebuild_uri(uri_string: str, query: str | None, expected_url: str):
    """Test rebuild_uri function with various URI configurations."""
    uri = urllib.parse.urlparse(uri_string)
    result = rebuild_uri(uri, query=query)
    assert result.geturl() == expected_url


@pytest.mark.parametrize(
    "upload_uri,keys,show_secrets,expected",
    [
        pytest.param(
            "https://example.com/path?apikey=secret123",
            ["apikey"],
            False,
            f"https://example.com/path?apikey={'*' * SECRET_STRING_LENGTH}",
            id="hide-single-secret",
        ),
        pytest.param(
            "https://example.com/path?apikey=secret123",
            ["apikey"],
            True,
            "https://example.com/path?apikey=secret123",
            id="show-single-secret",
        ),
        pytest.param(
            "https://example.com/path?apikey=secret123&token=mytoken",
            ["apikey", "token"],
            False,
            f"https://example.com/path?apikey={'*' * SECRET_STRING_LENGTH}&token={'*' * SECRET_STRING_LENGTH}",
            id="hide-multiple-secrets",
        ),
        pytest.param(
            "https://example.com/path?apikey=secret123&token=mytoken",
            ["apikey", "token"],
            True,
            "https://example.com/path?apikey=secret123&token=mytoken",
            id="show-multiple-secrets",
        ),
        pytest.param(
            "https://example.com/path?apikey=secret123&public=value",
            ["apikey"],
            False,
            f"https://example.com/path?apikey={'*' * SECRET_STRING_LENGTH}&public=value",
            id="hide-secret-keep-public",
        ),
        pytest.param(
            "https://example.com/path?public=value",
            ["apikey"],
            False,
            "https://example.com/path?public=value",
            id="no-matching-secret-key",
        ),
        pytest.param(
            "https://example.com/path",
            ["apikey"],
            False,
            "https://example.com/path",
            id="no-query-parameters",
        ),
        pytest.param(
            "s3://bucket/path?key=secret&accesskey=mykey",
            ["key", "accesskey"],
            False,
            f"s3://bucket/path?key={'*' * SECRET_STRING_LENGTH}&accesskey={'*' * SECRET_STRING_LENGTH}",
            id="s3-uri-with-secrets",
        ),
        pytest.param(
            "sftp://user@host/path?password=secret",
            ["password"],
            False,
            f"sftp://user@host/path?password={'*' * SECRET_STRING_LENGTH}",
            id="sftp-uri-with-password",
        ),
        pytest.param(
            "https://example.com/path?key=value1&key=value2",
            ["key"],
            False,
            f"https://example.com/path?key={'*' * SECRET_STRING_LENGTH}",
            id="multiple-values-same-key",
        ),
    ],
)
def test_safe_upload_uri(
    upload_uri: str, *, keys: list[str], show_secrets: bool, expected: str
):
    """Test safe_upload_uri function with various URIs and secret keys."""
    result = safe_upload_uri(upload_uri, keys=keys, show_secrets=show_secrets)
    assert result == expected


@pytest.mark.parametrize(
    "upload_uri,keys,show_secrets,expected",
    [
        pytest.param(
            "invalid-uri-without-scheme",
            ["apikey"],
            False,
            "invalid-uri-without-scheme",
            id="invalid-uri-returns-original",
        ),
        pytest.param(
            "https://[invalid-host]/path",
            ["apikey"],
            False,
            "https://[invalid-host]/path",
            id="invalid-host-returns-original",
        ),
    ],
)
def test_safe_upload_uri_with_invalid_input(
    upload_uri: str, *, keys: list[str], show_secrets: bool, expected: str
):
    """Test safe_upload_uri function handles invalid URIs gracefully."""
    result = safe_upload_uri(upload_uri, keys=keys, show_secrets=show_secrets)
    assert result == expected


def test_build_task_upload_uris_hide_secrets():
    """Test build_task_upload_uris hides secrets in all upload URIs."""
    task = MagicMock()
    task.upload.zim.upload_uri = "sftp://uploader@example.com:22/zim?apikey=secret123"
    task.upload.logs.upload_uri = (
        "s3://s3.us-east-1.example.com/?token=mytoken&bucketName=zim-bucket"
    )
    task.upload.artifacts.upload_uri = (
        "s3://s3.us-east-1.example.com/?token=mytoken&bucketName=artifacts-bucket"
    )

    keys = ["apikey", "token", "accesskey"]
    result = build_task_upload_uris(task, keys=keys, show_secrets=False)

    expected_mask = "*" * SECRET_STRING_LENGTH
    assert (
        result.upload.zim
        and result.upload.zim.upload_uri
        == f"sftp://uploader@example.com:22/zim?apikey={expected_mask}"
    )
    assert (
        result.upload.logs
        and result.upload.logs.upload_uri
        == f"s3://s3.us-east-1.example.com/?token={expected_mask}&bucketName=zim-bucket"
    )
    assert (
        result.upload.artifacts
        and result.upload.artifacts.upload_uri
        == f"s3://s3.us-east-1.example.com/?token={expected_mask}&bucketName=artifacts-bucket"
    )


def test_build_task_upload_uris_show_secrets():
    """Test build_task_upload_uris shows secrets when requested."""
    task = MagicMock()
    task.upload.zim.upload_uri = "sftp://uploader@example.com:22/zim?apikey=secret123"
    task.upload.logs.upload_uri = (
        "s3://s3.us-east-1.example.com/?token=mytoken&bucketName=logs-bucket"
    )
    task.upload.artifacts.upload_uri = (
        "s3://s3.us-east-1.example.com/?accesskey=mykey&bucketName=artifacts-bucket"
    )

    keys = ["apikey", "token", "accesskey"]
    result = build_task_upload_uris(task, keys=keys, show_secrets=True)

    # Check that secrets are visible
    assert (
        result.upload.zim
        and result.upload.zim.upload_uri
        == "sftp://uploader@example.com:22/zim?apikey=secret123"
    )
    assert (
        result.upload.logs
        and result.upload.logs.upload_uri
        == "s3://s3.us-east-1.example.com/?token=mytoken&bucketName=logs-bucket"
    )
    assert (
        result.upload.artifacts
        and result.upload.artifacts.upload_uri
        == "s3://s3.us-east-1.example.com/?accesskey=mykey&bucketName=artifacts-bucket"
    )


def test_build_task_upload_uris_no_secrets_in_uri():
    """Test build_task_upload_uris with URIs that don't contain any secrets."""

    task = MagicMock()
    task.upload.zim.upload_uri = "sftp://uploader@example.com:22/zim"
    task.upload.logs.upload_uri = (
        "s3://s3.us-east-1.example.com/?bucketName=logs-bucket"
    )
    task.upload.artifacts.upload_uri = (
        "s3://s3.us-east-1.example.com/?bucketName=artifacts-bucket"
    )

    keys = ["apikey", "token", "accesskey"]
    result = build_task_upload_uris(task, keys=keys, show_secrets=False)

    # URIs should remain unchanged
    assert (
        result.upload.zim
        and result.upload.zim.upload_uri == "sftp://uploader@example.com:22/zim"
    )
    assert (
        result.upload.logs
        and result.upload.logs.upload_uri
        == "s3://s3.us-east-1.example.com/?bucketName=logs-bucket"
    )
    assert (
        result.upload.artifacts
        and result.upload.artifacts.upload_uri
        == "s3://s3.us-east-1.example.com/?bucketName=artifacts-bucket"
    )


@pytest.mark.parametrize(
    "uri,filename,expected",
    [
        pytest.param(
            "https://example.com/path",
            "file.txt",
            "https://example.com/path/file.txt",
            id="https-uri-with-path",
        ),
        pytest.param(
            "https://example.com",
            "file.txt",
            "https://example.com/file.txt",
            id="https-uri-no-path",
        ),
        pytest.param(
            "s3://s3.example.com/path",
            "file.zim",
            "https://s3.example.com/path/file.zim",
            id="s3-uri-without-bucket",
        ),
        pytest.param(
            "s3://s3.example.com/path?bucketName=my-bucket",
            "file.zim",
            "https://s3.example.com/path/my-bucket/file.zim",
            id="s3-uri-with-bucket",
        ),
        pytest.param(
            "s3+https://s3.example.com/path?bucketName=my-bucket",
            "file.zim",
            "https://s3.example.com/path/my-bucket/file.zim",
            id="s3+https-uri-with-bucket",
        ),
        pytest.param(
            "s3://s3.us-east-1.example.com/?bucketName=zim-bucket&token=secret",
            "wikipedia_en_all.zim",
            "https://s3.us-east-1.example.com/zim-bucket/wikipedia_en_all.zim",
            id="s3-uri-with-bucket-and-other-params",
        ),
    ],
)
def test_upload_url(uri: str, filename: str, expected: str):
    """Test upload_url function with various URI schemes and filenames."""
    result = upload_url(uri, filename)
    assert result == expected


def test_upload_url_with_invalid_uri():
    result = upload_url("not a valid uri at all", "file.zim")
    assert result == "file.zim"
