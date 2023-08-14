import logging
from urllib.parse import urlparse

from common.constants import SECRET_REPLACEMENT
from common.schemas.models import ScheduleConfigSchema
from utils.offliners import build_str_command

logger = logging.getLogger(__name__)


def remove_secrets_from_response(response: dict):
    """replaces or removes (in-place) all occurences of secrets"""
    remove_secret_flags(response)
    remove_upload_secrets(response)


def remove_secret_flags(response: dict):
    """replaces (in-place) all occurences of secret flags with stars"""

    # we need flags to retrieve the secret value and replace it where we find it
    # in commands
    if "config" not in response or "flags" not in response["config"]:
        return

    schema = ScheduleConfigSchema.get_offliner_schema(
        response["config"]["task_name"]
    )().to_desc()
    fields = [field["data_key"] for field in schema if field.get("secret", False)]

    flags = response["config"]["flags"]

    # look after each fields of schema in flags
    for field in fields:
        if field not in flags:
            continue

        secret_flag_value = flags[field]

        flags[field] = SECRET_REPLACEMENT

        for separator in ["", "'", '"']:
            secret_command_value = (
                f"--{field}={separator}{secret_flag_value}{separator}"
            )
            remove_secret_flag_from_command(
                response, "config", field, secret_command_value
            )

            if "container" in response:
                remove_secret_flag_from_command(
                    response, "container", field, secret_command_value
                )

    # rebuild str_command from command
    if "str_command" in response["config"]:
        response["config"]["str_command"] = build_str_command(
            response["config"]["command"]
        )


def remove_secret_flag_from_command(
    response: dict, root_key_value: str, field_name: str, secret_value: str
):
    if "command" not in response[root_key_value]:
        return
    if secret_value not in response[root_key_value]["command"]:
        return
    index = response[root_key_value]["command"].index(secret_value)
    response[root_key_value]["command"][
        index
    ] = f'--{field_name}="{SECRET_REPLACEMENT}"'


def remove_upload_secrets(response: dict):
    """remove keyId and secretAccessKey upload_uri, since we upload logs to
    S3 but still need the rest of the URL to download scraper logs"""
    if (
        "upload" in response
        and "logs" in response["upload"]
        and "upload_uri" in response["upload"]["logs"]
    ):
        url = urlparse(response["upload"]["logs"]["upload_uri"])
        response["upload"]["logs"]["upload_uri"] = url._replace(
            query="&".join(
                [
                    param
                    for param in url.query.split("&")
                    if not param.lower().startswith("keyid")
                    and not param.lower().startswith("secretaccesskey")
                ]
            )
        ).geturl()
