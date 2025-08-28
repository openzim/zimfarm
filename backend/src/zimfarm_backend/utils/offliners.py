import pathlib
import shlex
from typing import Any, NamedTuple

from pydantic import AnyUrl

from zimfarm_backend.common import constants
from zimfarm_backend.common.enums import Offliner
from zimfarm_backend.common.schemas.models import (
    ExpandedScheduleConfigSchema,
    ResourcesSchema,
    ScheduleConfigSchema,
)
from zimfarm_backend.common.schemas.offliners.gutenberg import GutenbergFlagsSchema
from zimfarm_backend.common.schemas.offliners.phet import PhetFlagsSchema
from zimfarm_backend.common.schemas.offliners.sotoki import SotokiFlagsSchema
from zimfarm_backend.common.schemas.offliners.zimit import (
    ZimitFlagsSchema,
    ZimitFlagsSchemaRelaxed,
)


class OfflinerDefinition(NamedTuple):
    cmd: str
    std_output: bool | str
    std_stats: bool | str


OFFLINER_DEFS: dict[Offliner, OfflinerDefinition] = {
    Offliner.freecodecamp: OfflinerDefinition("fcc2zim", True, False),
    Offliner.gutenberg: OfflinerDefinition("gutenberg2zim", False, False),
    Offliner.sotoki: OfflinerDefinition("sotoki", True, True),
    Offliner.wikihow: OfflinerDefinition("wikihow2zim", True, True),
    Offliner.ifixit: OfflinerDefinition("ifixit2zim", True, True),
    Offliner.mwoffliner: OfflinerDefinition("mwoffliner", "outputDirectory", False),
    Offliner.youtube: OfflinerDefinition("youtube2zim", True, False),
    Offliner.ted: OfflinerDefinition("ted2zim", True, False),
    Offliner.openedx: OfflinerDefinition("openedx2zim", True, False),
    Offliner.nautilus: OfflinerDefinition("nautiluszim", True, False),
    Offliner.zimit: OfflinerDefinition("zimit", True, "zimit-progress-file"),
    Offliner.kolibri: OfflinerDefinition("kolibri2zim", True, False),
    Offliner.devdocs: OfflinerDefinition("devdocs2zim", True, False),
    Offliner.mindtouch: OfflinerDefinition("mindtouch2zim", True, True),
    Offliner.phet: OfflinerDefinition("phet2zim", False, False),
}


def mount_point_for(offliner: Offliner) -> pathlib.Path:
    """Path to mount task volume in scraper"""
    if offliner == Offliner.phet:
        return pathlib.Path("/phet/dist")
    return pathlib.Path("/output")


def docker_config_for(
    offliner: Offliner, resources: ResourcesSchema
) -> ResourcesSchema:
    # Note: in docker, --shm-size sets the size of /dev/shm
    # it is taken out of --memory (if set)
    if offliner == Offliner.zimit:
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
    offliner: Offliner,
    config: ScheduleConfigSchema,
    mount_point: pathlib.Path,
    *,
    show_secrets: bool = True,
) -> list[str]:
    """Command list to be passed to docker run."""
    offliner_def = OFFLINER_DEFS[offliner]
    cmd = offliner_def.cmd

    if isinstance(config.offliner, SotokiFlagsSchema):
        config.offliner.mirror = config.offliner.mirror or AnyUrl(
            "https://s3.us-west-1.wasabisys.com/org-kiwix-stackexchange"
        )
        config.offliner.redis_url = "unix:///var/run/redis.sock"
        config.offliner.keep_redis = True

    if isinstance(config.offliner, ZimitFlagsSchema | ZimitFlagsSchemaRelaxed):
        if config.offliner.admin_email is None:
            config.offliner.admin_email = "contact+zimfarm@kiwix.org"
        if config.offliner.keep is None:
            # always keep temporary files, they will be deleted anyway
            config.offliner.keep = True

    # Set default publisher. The "publisher" flag is set if a default is provided in the
    # local environment and if it is not already set manually. For a scraper to be
    # integrated into Zimfarm it is now a requirement that a flag "publisher" is present
    # and named like this.

    if (
        not isinstance(config.offliner, PhetFlagsSchema)
        and constants.DEFAULT_PUBLISHER
        and not config.offliner.publisher
    ):
        config.offliner.publisher = constants.DEFAULT_PUBLISHER

    offliner_flags = config.offliner.model_dump(
        mode="json", context={"show_secrets": show_secrets}
    )

    if offliner_def.std_output:
        offliner_flags[
            (
                offliner_def.std_output
                if isinstance(offliner_def.std_output, str)
                else "output"
            )
        ] = str(mount_point)

    if offliner_def.std_stats:
        offliner_flags[
            (
                offliner_def.std_stats
                if isinstance(offliner_def.std_stats, str)
                else "stats-filename"
            )
        ] = str(mount_point_for(offliner) / "task_progress.json")

    if isinstance(config.offliner, GutenbergFlagsSchema):
        # multiple ZIM expects a directory
        if config.offliner.one_language_one_zim:
            offliner_flags["one-language-one-zim"] = str(mount_point)
        if config.offliner.one_language_one_zim is False:
            del offliner_flags["one-language-one-zim"]
    # compute the flag options
    return [cmd, *compute_flags(offliner_flags)]


def expanded_config(
    config: ScheduleConfigSchema, *, show_secrets: bool = True
) -> ExpandedScheduleConfigSchema:
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

    offliner_id = Offliner(config.offliner.offliner_id)
    # offliners can specify additional docker options (capabilities)

    new_resources = docker_config_for(offliner_id, config.resources)

    dev_shm = get_shm(
        offliner_shm=new_resources.shm,
        config_resources=config.resources,
    )

    if dev_shm:
        new_resources.shm = dev_shm

    mount_point = mount_point_for(offliner_id)
    command = command_for(offliner_id, config, mount_point, show_secrets=show_secrets)

    return ExpandedScheduleConfigSchema.model_validate(
        {
            "warehouse_path": config.warehouse_path,
            "resources": new_resources,
            "offliner": config.offliner,
            "platform": config.platform,
            "artifacts_globs": config.artifacts_globs,
            "monitor": config.monitor,
            "image": {
                "name": Offliner.get_image_name(offliner_id),
                "tag": config.image.tag,
            },
            "mount_point": mount_point,
            "command": command,
            "str_command": " ".join(command),
        },
        context={"skip_validation": True},
    )


def get_key_differences(d1: dict[str, Any], d2: dict[str, Any]) -> list[str]:
    """Return the keys that are in d1 but not in d2"""
    return list(set(d1.keys()) - set(d2.keys()))
