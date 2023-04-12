from typing import Any, Type

from common.constants import SECRET_REPLACEMENT
from common.schemas.models import ScheduleConfigSchema
from utils.offliners import build_str_command


def remove_secrets_from_response(response: dict):
    """replaces (in-place) all occurences of secrets in flags/commands with stars"""

    if "config" not in response:
        return

    schema = ScheduleConfigSchema.get_offliner_schema(
        response["config"]["task_name"]
    )().to_desc()
    fields = [flag["data_key"] for flag in schema if flag.get("secret", False)]

    for field in fields:
        flags = response["config"]["flags"]
        command = response["config"]["command"]
        if field in flags:
            index = command.index(f'--{field}="{flags[field]}"')
            command[index] = f'--{field}="{SECRET_REPLACEMENT}"'
            flags[field] = SECRET_REPLACEMENT
            if "container" in response:
                response["container"]["command"][
                    index
                ] = f'--{field}="{SECRET_REPLACEMENT}"'
        response["config"]["str_command"] = build_str_command(
            response["config"]["command"]
        )


def raise_if_none(
    object_to_check: Any, exception_class: Type[Exception], *exception_args: object
) -> None:
    raise_if(object_to_check is None, exception_class, exception_args)


def raise_if(
    condition: bool, exception_class: Type[Exception], *exception_args: object
) -> None:
    if condition:
        raise exception_class(*exception_args)
