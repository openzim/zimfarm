import pathlib
import urllib.parse

from zimfarm_backend import logger
from zimfarm_backend.common.constants import SECRET_STRING_LENGTH
from zimfarm_backend.common.schemas.orms import RequestedTaskFullSchema, TaskFullSchema


def rebuild_uri(
    uri: urllib.parse.ParseResult,
    scheme: str | None = None,
    username: str | None = None,
    password: str | None = None,
    hostname: str | None = None,
    port: int | None = None,
    path: str | None = None,
    query: str | None = None,
):
    scheme = scheme if scheme is not None else uri.scheme
    username = username if username is not None else uri.username
    password = password if password is not None else uri.password
    hostname = hostname if hostname is not None else uri.hostname
    port = port if port is not None else uri.port
    path = path if path is not None else uri.path
    netloc = ""
    if username:
        netloc += username
    if password:
        netloc += f":{password}"
    if username or password:
        netloc += "@"
    if hostname:
        netloc += hostname
    if port:
        netloc += f":{port}"
    query = query if query is not None else uri.query
    fragment = uri.fragment
    return urllib.parse.urlparse(
        urllib.parse.urlunparse([scheme, netloc, path, fragment, query, fragment])
    )


def safe_upload_uri(
    upload_uri: str, *, keys: list[str], show_secrets: bool = True
) -> str:
    """Get a new URI by hiding/showing values of keys in query parameters"""
    try:
        uri = urllib.parse.urlparse(upload_uri)
        pathlib.Path(uri.path)
    except Exception as exc:
        logger.exception(f"invalid upload URI: `{upload_uri}` ({exc}).")
        return upload_uri

    params = urllib.parse.parse_qs(uri.query)
    param_keys = params.keys()
    for key in keys:
        if key in param_keys and not show_secrets:
            params[key] = [SECRET_STRING_LENGTH * "*"]

    return urllib.parse.unquote(
        rebuild_uri(uri, query=urllib.parse.urlencode(params, doseq=True)).geturl()
    )


def build_task_upload_uris(
    task: TaskFullSchema | RequestedTaskFullSchema,
    *,
    keys: list[str],
    show_secrets: bool = True,
) -> TaskFullSchema | RequestedTaskFullSchema:
    if task.upload.zim and task.upload.zim.upload_uri:
        task.upload.zim.upload_uri = safe_upload_uri(
            task.upload.zim.upload_uri, keys=keys, show_secrets=show_secrets
        )
    if task.upload.logs and task.upload.logs.upload_uri:
        task.upload.logs.upload_uri = safe_upload_uri(
            task.upload.logs.upload_uri, keys=keys, show_secrets=show_secrets
        )
    if task.upload.artifacts and task.upload.artifacts.upload_uri:
        task.upload.artifacts.upload_uri = safe_upload_uri(
            task.upload.artifacts.upload_uri, keys=keys, show_secrets=show_secrets
        )
    if task.upload.check and task.upload.check.upload_uri:
        task.upload.check.upload_uri = safe_upload_uri(
            task.upload.check.upload_uri, keys=keys, show_secrets=show_secrets
        )
    return task


def upload_url(uri: str, filename: str) -> str:
    """Generate a display URL for an upload based on the URI scheme."""
    url = urllib.parse.urlparse(uri)
    scheme = url.scheme

    # If scheme is not http or https, convert to https
    if scheme not in ["http", "https"]:
        url = urllib.parse.urlparse(uri.replace(url.scheme + ":", "https:"))

    # Handle S3 scheme
    if scheme in ["s3", "s3+http", "s3+https"]:
        download_url = f"{url.scheme}://{url.netloc}{url.path}"

        if not download_url.endswith("/"):
            download_url += "/"
        # Extract bucketName from query parameters
        params = urllib.parse.parse_qs(url.query)
        bucket_name = params.get("bucketName", [None])[0]

        if bucket_name:
            download_url += bucket_name + "/"

        return download_url + filename

    # For http/https schemes, return full URL with filename
    if scheme in ["http", "https"]:
        # Ensure path ends with / before adding filename
        path = url.path
        if path and not path.endswith("/"):
            path += "/"
        elif not path:
            path = "/"

        return f"{url.scheme}://{url.netloc}{path}{filename}"

    return filename
