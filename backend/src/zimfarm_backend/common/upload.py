import pathlib
import urllib.parse

from zimfarm_backend import logger
from zimfarm_backend.common.constants import SECRET_STRING_LENGTH
from zimfarm_backend.common.schemas.orms import RequestedTaskFullSchema, TaskFullSchema


def rebuild_uri(uri: urllib.parse.ParseResult, query: str | None = None):
    scheme = uri.scheme
    username = uri.username
    password = uri.password
    hostname = uri.hostname or ""
    port = uri.port
    path = uri.path
    netloc = ""
    if username:
        netloc += username
    if password:
        netloc += f":{password}"
    if username or password:
        netloc += "@"
    netloc += hostname
    if port:
        netloc += f":{port}"
    query = query or uri.query
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
    return task
