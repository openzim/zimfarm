import pathlib
import shlex
from copy import deepcopy
from os import getenv
from typing import Any

from pydantic.alias_generators import to_camel

from zimfarm_backend.common import constants
from zimfarm_backend.common.schemas.models import (
    ExpandedRecipeConfigSchema,
    RecipeConfigSchema,
    ResourcesSchema,
)
from zimfarm_backend.common.schemas.offliners.models import (
    FlagSchema,
    OfflinerSpecSchema,
)
from zimfarm_backend.common.schemas.orms import OfflinerDefinitionSchema, OfflinerSchema


def mount_point_for(offliner: OfflinerSchema) -> pathlib.Path:
    """Path to mount task volume in scraper"""
    if offliner.id == "phet":
        return pathlib.Path("/phet/dist")
    return pathlib.Path("/output")


def docker_config_for(
    offliner: OfflinerSchema, resources: ResourcesSchema
) -> ResourcesSchema:
    # Note: in docker, --shm-size sets the size of /dev/shm
    # it is taken out of --memory (if set)
    if offliner.id == "zimit":
        return resources.model_copy(update={"shm": 2**30})
    return resources


def simplified(value: Any) -> str:
    if (isinstance(value, float) and value.is_integer()) or str(value).isdigit():
        return str(int(value))
    return str(value)


def compute_flags(
    flags: dict[str, str | bool | list[str] | None], *, use_equals: bool = True
) -> list[str]:
    """flat list of params from dict of flags"""
    params: list[str] = []
    for key, value in flags.items():
        if key in ("offliner_id", "offlinerId", "offliner-id"):
            continue

        if value is True:
            params.append(f"--{key}")
            continue

        if value is False:
            continue

        if value is None:
            continue

        elif isinstance(value, list):
            for item in value:
                if use_equals:
                    params.append(f"--{key}={shlex.quote(simplified(item))}")
                else:
                    params.append(f"--{key}")
                    params.append(shlex.quote(simplified(item)))
        elif use_equals:
            params.append(f"--{key}={shlex.quote(simplified(value))}")
        else:
            params.append(f"--{key}")
            params.append(shlex.quote(simplified(value)))
    return params


def command_for(
    offliner: OfflinerSchema,
    offliner_definition: OfflinerDefinitionSchema,
    config: RecipeConfigSchema,
    mount_point: pathlib.Path,
    *,
    show_secrets: bool = True,
) -> list[str]:
    """Command list to be passed to docker run."""

    # Set default publisher. The "publisher" flag is set if a default is provided in the
    # local environment and if it is not already set manually. For a scraper to be
    # integrated into Zimfarm it is now a requirement that a flag "publisher" is present
    # and named like this.

    # find the field_name which has is_publisher set from the definition
    field_name = next(
        (
            field
            for field, flags in offliner_definition.schema_.flags.items()
            if flags.is_publisher
        ),
        None,
    )

    if (
        field_name
        and constants.DEFAULT_PUBLISHER
        and not getattr(config.offliner, field_name)
    ):
        setattr(config.offliner, field_name, constants.DEFAULT_PUBLISHER)

    offliner_flags = config.offliner.model_dump(
        mode="json", context={"show_secrets": show_secrets}
    )

    if offliner_definition.schema_.std_output:
        offliner_flags[
            (
                offliner_definition.schema_.std_output
                if isinstance(offliner_definition.schema_.std_output, str)
                else "output"
            )
        ] = str(mount_point)

    if offliner_definition.schema_.std_stats:
        offliner_flags[
            (
                offliner_definition.schema_.std_stats
                if isinstance(offliner_definition.schema_.std_stats, str)
                else "stats-filename"
            )
        ] = str(mount_point_for(offliner) / "task_progress.json")

    if offliner.id == "gutenberg":
        # multiple ZIM expects a directory
        if (
            hasattr(config.offliner, "one_language_one_zim")
            and config.offliner.one_language_one_zim  # pyright: ignore[reportAttributeAccessIssue,reportUnknownMemberType]
        ):
            offliner_flags["one-language-one-zim"] = str(mount_point)
        if (
            hasattr(config.offliner, "one_language_one_zim")
            and config.offliner.one_language_one_zim  # pyright: ignore[reportAttributeAccessIssue,reportUnknownMemberType]
            is False
        ):
            del offliner_flags["one-language-one-zim"]
    # compute the flag options
    return [offliner.command_name, *compute_flags(offliner_flags)]


def get_image_prefix(offliner: str) -> str:
    prefix = getenv(f"DOCKER_REGISTRY_{offliner}", default="ghcr.io")
    prefix += "/" if prefix else ""
    return prefix


def get_image_name(offliner: str) -> str:
    return get_image_prefix(offliner) + offliner


def expanded_config(
    config: RecipeConfigSchema,
    offliner: OfflinerSchema,
    offliner_definition: OfflinerDefinitionSchema,
    *,
    show_secrets: bool = True,
) -> ExpandedRecipeConfigSchema:
    def get_shm(
        offliner_shm: int | None, config_resources: ResourcesSchema
    ) -> int | None:
        # use largest of /dev/shm specified (in config vs in offliner rule)
        if offliner_shm and config_resources.shm:
            dev_shm = max([offliner_shm, config_resources.shm])
        else:
            dev_shm = config_resources.shm or offliner_shm

        # use at most memory for /dev/shm if specified and above memory
        if dev_shm and dev_shm > config_resources.memory:
            dev_shm = config_resources.memory
        return dev_shm

    # offliners can specify additional docker options (capabilities)

    new_resources = docker_config_for(offliner, config.resources)

    dev_shm = get_shm(
        offliner_shm=new_resources.shm,
        config_resources=config.resources,
    )

    if dev_shm:
        new_resources.shm = dev_shm

    mount_point = mount_point_for(offliner)
    command = command_for(
        offliner, offliner_definition, config, mount_point, show_secrets=show_secrets
    )

    return ExpandedRecipeConfigSchema.model_validate(
        {
            "warehouse_path": config.warehouse_path,
            "resources": new_resources,
            "offliner": config.offliner,
            "platform": config.platform,
            "artifacts_globs": config.artifacts_globs,
            "monitor": config.monitor,
            "image": {
                "name": get_image_name(offliner.docker_image_name),
                "tag": config.image.tag,
            },
            "mount_point": mount_point,
            "command": command,
            "str_command": " ".join(command),
        },
        context={"skip_validation": True},
    )


def get_key_differences(d1: dict[str, Any], d2: dict[str, Any]) -> list[str]:
    """Return the keys that are in d1 but not in d2.

    This does not recurse into nested dictionaries.
    """
    return list(set(d1.keys()) - set(d2.keys()))


def flag_alias(flag_name: str, flag: FlagSchema, base_model: str) -> str:
    """Return the alias used in the database for a flag."""
    if flag.alias:
        return flag.alias
    if base_model == "CamelModel":
        return to_camel(flag_name)
    elif base_model == "DashModel":
        return flag_name.replace("_", "-")
    else:
        raise ValueError(
            f"Cannot determine alias for unknown base model '{base_model}'"
        )


def clear_unset_choices_dependents(
    spec: OfflinerSpecSchema, config: dict[str, Any], base_model: str
) -> dict[str, Any]:
    """Clear the values of the flags marked as dependents if choice wasn't selected"""
    config = deepcopy(config)
    for flag_name, flag in spec.flags.items():
        if not flag.choices:
            continue
        selected_value = config.get(
            flag_name, config.get(flag_alias(flag_name, flag, base_model))
        )
        if selected_value is None:
            # Enum is an optional field and nothing was selected
            continue

        for choice in flag.choices:
            if isinstance(choice, str):
                continue

            if choice.value == selected_value:
                continue

            # Clear the flags specified in the dependents as this choice option was
            # not selected
            for dependent in choice.dependents:
                if dependent in config:
                    del config[dependent]

                alias = flag_alias(dependent, spec.flags[dependent], base_model)
                if alias in config:
                    del config[alias]

    return config
