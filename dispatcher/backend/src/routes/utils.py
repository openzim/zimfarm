import logging
from urllib.parse import urlparse

from common.constants import SECRET_REPLACEMENT
from common.schemas.models import ScheduleConfigSchema
from utils.offliners import build_str_command

logger = logging.getLogger(__name__)


def remove_secrets_from_response(response: dict):
    """replaces or removes (in-place) all occurences of secrets"""
    remove_upload_secrets_from_flags_and_commands(response)
    remove_upload_secrets_from_response(response)


def remove_upload_secrets_from_flags_and_commands(response: dict):
    """replaces (in-place) all occurences of secrets in flags/commands with stars"""

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

        secret_command_value = f'--{field}="{secret_flag_value}"'

        if (
            "command" in response["config"]
            and secret_command_value in response["config"]["command"]
        ):
            index = response["config"]["command"].index(secret_command_value)
            response["config"]["command"][index] = f'--{field}="{SECRET_REPLACEMENT}"'

        if (
            "container" in response
            and "command" in response["container"]
            and secret_command_value in response["container"]["command"]
        ):
            index = response["container"]["command"].index(secret_command_value)
            response["container"]["command"][
                index
            ] = f'--{field}="{SECRET_REPLACEMENT}"'

    # rebuild str_command from command
    if "str_command" in response["config"]:
        response["config"]["str_command"] = build_str_command(
            response["config"]["command"]
        )


def remove_upload_secrets_from_response(response: dict):
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
