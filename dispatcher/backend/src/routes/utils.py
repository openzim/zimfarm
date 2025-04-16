import logging
from typing import Any, Dict, List
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

import sqlalchemy as sa
from common.constants import SECRET_REPLACEMENT
from common.schemas.models import ScheduleConfigSchema

from utils.offliners import build_str_command

logger = logging.getLogger(__name__)


def has_dict_sub_key(data: Dict[str, Any], keys: List[str]):
    """check if dictionnary has the list of sub-keys present

    Very permisive in terms of dict structure, i.e. any key in the path might be either
    missing or None, this will work
    """
    cur_data = data
    for key in keys:
        if key not in cur_data or not cur_data[key]:
            return False
        cur_data = cur_data[key]
    return True


def remove_secrets_from_response(response: dict):
    """replaces or removes (in-place) all occurences of secrets"""
    remove_secret_flags(response)
    remove_url_secrets(response)


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
    if has_dict_sub_key(response, ["config", "str_command"]):
        response["config"]["str_command"] = build_str_command(
            response["config"]["command"]
        )


def remove_secret_flag_from_command(
    response: dict, root_key_value: str, field_name: str, secret_value: str
):
    """remove one secret flag from command (either for container or config)"""
    if not has_dict_sub_key(response, [root_key_value, "command"]):
        return
    if secret_value not in response[root_key_value]["command"]:
        return
    index = response[root_key_value]["command"].index(secret_value)
    response[root_key_value]["command"][
        index
    ] = f'--{field_name}="{SECRET_REPLACEMENT}"'


def remove_url_secrets(response: dict):
    """remove secrets from any URL we might find

    For now we remove:
    - password if passed in the network location
    - keyId and secretAccessKey query params (probably used for S3)
    """
    for key in response.keys():
        if not response[key]:
            continue
        if isinstance(response[key], dict):
            remove_url_secrets(response[key])
        else:
            if not isinstance(response[key], str) or "://" not in response[key]:
                continue
            for url in [word for word in response[key].split() if "://" in word]:
                try:
                    urlparts = urlsplit(url)
                except Exception as exc:
                    logger.warning(
                        f"Ignoring bad URL in remove_url_secrets: {url}", exc_info=exc
                    )
                    continue
                newquery = urlencode(
                    {
                        key: (
                            value
                            if str(key).lower() not in ["keyid", "secretaccesskey"]
                            else SECRET_REPLACEMENT
                        )
                        for key, values in parse_qs(urlparts.query).items()
                        for value in values
                    },
                    doseq=True,
                )
                newnetloc: str | None = urlparts.netloc
                if newnetloc and urlparts.password:
                    newnetloc = newnetloc.replace(urlparts.password, SECRET_REPLACEMENT)
                secured_url = urlunsplit(
                    (
                        urlparts.scheme,
                        newnetloc,
                        urlparts.path,
                        newquery,
                        urlparts.fragment,
                    )
                )
                response[key] = response[key].replace(url, secured_url)


def apply_sort(stmt, sort_by, sort_order, model=None, join_models=None):
    """
    Apply sorting based on a sort field name and order.
    """
    join_models = join_models or {}
    
    def apply_sort_direction(field):
        """Apply sort direction to a field"""
        return field.desc() if sort_order == "desc" else field.asc()
    
    if not sort_by:
        return stmt.order_by(apply_sort_direction(model.updated_at))
    
    try:
        if sort_by == "priority":
            return stmt.order_by(apply_sort_direction(model.priority))
        
        elif sort_by == "updated_at":
            return stmt.order_by(apply_sort_direction(model.updated_at))
            
        elif sort_by == "schedule_name":
            return stmt.order_by(apply_sort_direction(join_models["Schedule"].name))
            
        elif sort_by == "worker" or sort_by == "worker_name":
            return stmt.order_by(apply_sort_direction(join_models["Worker"].name))
        
        elif sort_by == "timestamp.requested":
            field = model.timestamp["requested"]["$date"].astext.cast(sa.BigInteger)
            return stmt.order_by(apply_sort_direction(field))
            
        elif sort_by == "timestamp.reserved":
            field = model.timestamp["reserved"]["$date"].astext.cast(sa.BigInteger)
            return stmt.order_by(apply_sort_direction(field))
        elif model and hasattr(model, sort_by):
            return stmt.order_by(apply_sort_direction(getattr(model, sort_by)))
        logger.warning(f"Unknown sort field: {sort_by}")
        
    except Exception as e:
        logger.error(f"Error applying sorting: {e}")
        return stmt.order_by(apply_sort_direction(model.updated_at))