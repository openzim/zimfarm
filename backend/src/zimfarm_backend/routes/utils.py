# import logging
# from typing import Any, cast, get_args
# from urllib.parse import SplitResult, parse_qs, urlencode, urlsplit, urlunsplit
#
# import pydantic
#
# from zimfarm_backend.common.constants import SECRET_REPLACEMENT
# from zimfarm_backend.common.schemas.fields import (
#     OptionalZIMSecretStr,
#     S3OptimizationCache,
#     SecretStr,
#     ZIMSecretStr,
# )
# from zimfarm_backend.common.schemas.models import OfflinerSchema
# from zimfarm_backend.utils.offliners import build_str_command
#
# logger = logging.getLogger(__name__)
#
#
# def has_dict_sub_key(data: dict[str, Any], keys: list[str]):
#     """check if dictionnary has the list of sub-keys present
#
#     Very permisive in terms of dict structure, i.e. any key in the path might be
# either
#     missing or None, this will work
#     """
#     cur_data = data
#     for key in keys:
#         if key not in cur_data or not cur_data[key]:
#             return False
#         cur_data = cur_data[key]
#     return True
#
#
# def remove_secrets_from_payload(payload: dict[str, Any]):
#     """replaces or removes (in-place) all occurences of secrets"""
#     remove_secret_flags(payload)
#     remove_url_secrets(payload)
#
#
# def remove_secret_flags(response: dict[str, Any]):
#     """replaces (in-place) all occurences of secret flags with stars"""
#
#     # we need flags to retrieve the secret value and replace it where we find it
#     # in commands
#     if "config" not in response or "offliner" not in response["config"]:
#         return
#
#     # Get the offliner_id from the response
#     offliner_id = response["config"]["offliner"].get("offliner_id")
#     if not offliner_id:
#         return
#
#     # Get the schema class based on the offliner_id
#     schema_class = cast(
#         # pyright can't seem to determine the type of OfflinerSchema because
#         # it uses if..else. So, we show that schema_class is a class that
#         # inherits from pydantic.BaseModel
#         type[pydantic.BaseModel] | None,
#         next(
#             (
#                 schema
#                 for schema in get_args(OfflinerSchema)
#                 if get_args(schema.model_fields["offliner_id"].annotation)[0]
#                 == offliner_id
#             ),
#             None,
#         ),
#     )
#     if not schema_class:
#         return
#
#     fields: list[str] = [
#         field.alias
#         for field in schema_class.model_fields.values()
#         if field.alias
#         and field.annotation
#         in (
#             OptionalZIMSecretStr,
#             ZIMSecretStr,
#             S3OptimizationCache,
#         )
#     ]
#
#     flags = response["config"]["flags"]
#
#     # look after each fields of schema in flags
#     for field in fields:
#         if field not in flags:
#             continue
#
#         secret_flag_value = flags[field]
#
#         flags[field] = SECRET_REPLACEMENT
#
#         for separator in ["", "'", '"']:
#             secret_command_value = (
#                 f"--{field}={separator}{secret_flag_value}{separator}"
#             )
#             remove_secret_flag_from_command(
#                 response, "config", str(field), secret_command_value
#             )
#
#             if "container" in response:
#                 remove_secret_flag_from_command(
#                     response, "container", str(field), secret_command_value
#                 )
#
#     # rebuild str_command from command
#     if has_dict_sub_key(response, ["config", "str_command"]):
#         response["config"]["str_command"] = build_str_command(
#             response["config"]["command"]
#         )
#
#
# def remove_secret_flag_from_command(
#     response: dict[str, Any], root_key_value: str, field_name: str, secret_value: str
# ):
#     """remove one secret flag from command (either for container or config)"""
#     if not has_dict_sub_key(response, [root_key_value, "command"]):
#         return
#     if secret_value not in response[root_key_value]["command"]:
#         return
#     index = response[root_key_value]["command"].index(secret_value)
#     response[root_key_value]["command"][index] = (
#         f'--{field_name}="{SECRET_REPLACEMENT}"'
#     )
#
#
# def remove_url_secrets(response: dict[str, Any]):
#     """remove secrets from any URL we might find
#
#     For now we remove:
#     - password if passed in the network location
#     - keyId and secretAccessKey query params (probably used for S3)
#     """
#     for key, _ in response.items():
#         if not response[key]:
#             continue
#         if isinstance(response[key], dict):
#             remove_url_secrets(response[key])
#         else:
#             if not isinstance(response[key], str) or "://" not in response[key]:
#                 continue
#             for url in [word for word in response[key].split() if "://" in word]:
#                 try:
#                     urlparts = cast(SplitResult, urlsplit(url))
#                 except Exception as exc:
#                     logger.warning(
#                         f"Ignoring bad URL in remove_url_secrets: {url}", exc_info=exc
#                     )
#                     continue
#                 new_query = urlencode(
#                     {
#                         key: (
#                             value
#                             if str(key).lower() not in ["keyid", "secretaccesskey"]
#                             else SECRET_REPLACEMENT
#                         )
#                         for key, values in parse_qs(urlparts.query).items()
#                         for value in values
#                     },
#                     doseq=True,
#                 )
#                 new_netloc: str | None = urlparts.netloc
#                 if new_netloc and urlparts.password:
#                     new_netloc = new_netloc.replace(
#                         urlparts.password, SECRET_REPLACEMENT
#                     )
#                 secured_url = urlunsplit(
#                     (
#                         urlparts.scheme,
#                         new_netloc,
#                         urlparts.path,
#                         new_query,
#                         urlparts.fragment,
#                     )
#                 )
#                 response[key] = response[key].replace(url, secured_url)
