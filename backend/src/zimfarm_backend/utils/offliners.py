import pathlib
from typing import Any, NamedTuple

from zimfarm_backend.common import constants
from zimfarm_backend.common.enums import Offliner


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


def mount_point_for(offliner: Offliner):
    """Path to mount task volume in scraper"""
    if offliner == Offliner.phet:
        return pathlib.Path("/phet/dist")
    return pathlib.Path("/output")


def command_for(
    offliner: Offliner, flags: dict[str, Any], mount_point: pathlib.Path | str
) -> list[str]:
    """command:list to be passed to docker run

    for an offliner,  flags:dict and a mount_point:Path (task volume)"""

    offliner_def = OFFLINER_DEFS[offliner]
    cmd = offliner_def.cmd
    if offliner_def.std_output:
        flags[
            (
                offliner_def.std_output
                if isinstance(offliner_def.std_output, str)
                else "output"
            )
        ] = str(mount_point)
    if offliner_def.std_stats:
        flags[
            (
                offliner_def.std_stats
                if isinstance(offliner_def.std_stats, str)
                else "stats-filename"
            )
        ] = str(mount_point_for(offliner) / "task_progress.json")

    if offliner == Offliner.gutenberg:
        # multiple ZIM expects a directory
        if flags.get("one-language-one-zim"):
            flags["one-language-one-zim"] = str(mount_point)
        if flags.get("one-language-one-zim") is False:
            del flags["one-language-one-zim"]
        # when not using multiple ZIM, scraper uses cwd as output (/output)
    if offliner == Offliner.sotoki:
        flags["mirror"] = flags.get(
            "mirror", "https://s3.us-west-1.wasabisys.com/org-kiwix-stackexchange"
        )
        flags["redis-url"] = "unix:///var/run/redis.sock"
        flags["keep-redis"] = True
    if offliner == Offliner.zimit:
        if "adminEmail" not in flags:
            flags["adminEmail"] = "contact+zimfarm@kiwix.org"
        if "keep" not in flags:
            # always keep temporary files, they will be deleted anyway
            flags["keep"] = True

    _command_for_set_default_publisher(flags, offliner)

    return [cmd, *compute_flags(flags)]


def _command_for_set_default_publisher(flags: dict[str, Any], offliner: Offliner):
    """Set a default publisher in the command

    The "publisher" flag is set if a default is provided in the local environment and
    if it is not already set manually.

    For a scraper to be integrated into Zimfarm it is now a requirement that a flag
    "publisher" is present and named like this.
    """
    if (
        offliner != Offliner.phet
        and constants.DEFAULT_PUBLISHER
        and "publisher" not in flags
    ):
        flags["publisher"] = constants.DEFAULT_PUBLISHER


def docker_config_for(offliner: Offliner):
    # Note: in docker, --shm-size sets the size of /dev/shm
    # it is taken out of --memory (if set)
    extra_config: dict[str, Any] = {}
    if offliner == Offliner.zimit:
        extra_config.update({"shm": 2**30})
    return extra_config


def simplified(value: Any) -> str:
    if (isinstance(value, float) and value.is_integer()) or str(value).isdigit():
        return str(int(value))
    return str(value)


def compute_flags(
    flags: dict[str, str | bool | list[str]], *, use_equals: bool = True
) -> list[str]:
    """flat list of params from dict of flags"""
    params: list[str] = []
    for key, value in flags.items():
        if value is True:
            params.append(f"--{key}")
            continue
        if value is False:
            continue
        elif isinstance(value, list):
            for item in value:
                if use_equals:
                    params.append(f'--{key}="{simplified(item)}"')
                else:
                    params.append(f"--{key}")
                    params.append(f"{simplified(item)}")
        elif use_equals:
            params.append(f'--{key}="{simplified(value)}"')
        else:
            params.append(f"--{key}")
            params.append(f"{simplified(value)}")
    return params


def expanded_config(config: dict[str, Any]) -> dict[str, Any]:
    # update image name with registry if required
    config["image"]["name"] = Offliner.get_image_name(config["task_name"])

    # mount-point is offliner-specific
    config["mount_point"] = str(mount_point_for(config["task_name"]))
    # computed command flags
    config["command"] = command_for(
        config["task_name"], config["flags"], config["mount_point"]
    )
    # workers uses string version
    config["str_command"] = build_str_command(config["command"])
    # offliners can specify additional docker options (capabilities)
    docker_options = docker_config_for(config["task_name"])

    def get_shm(
        offliner_shm: int | None = None, config_shm: int | None = None
    ) -> int | None:
        # use largest of /dev/shm specified (in config vs in offliner rule)
        if offliner_shm and config_shm:
            dev_shm = max([offliner_shm, config_shm])
        else:
            dev_shm = config_shm or offliner_shm

        # use at most memory for /dev/shm if specified and above memory
        if dev_shm and dev_shm > config["resources"]["memory"]:
            dev_shm = config["resources"]["memory"]
        return dev_shm

    dev_shm = get_shm(
        offliner_shm=docker_options.pop("shm", None),
        config_shm=config["resources"].get("shm"),
    )
    if dev_shm:
        config["resources"]["shm"] = dev_shm

    # offliners can update resources
    config["resources"].update(docker_options)

    return config


def build_str_command(args: list[str]) -> str:
    """string version of the command to be run by the worker"""
    return " ".join(args)
