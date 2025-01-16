import argparse
from pathlib import Path

from recipesauto.constants import NAME, VERSION
from recipesauto.context import Context


def prepare_context(raw_args: list[str]) -> None:
    """Initialize scraper context from command line arguments"""

    parser = argparse.ArgumentParser(
        prog=NAME,
    )

    def _parse_context_values(value: str) -> dict[str, str]:
        return {
            context.split("=")[0]: context.split("=", maxsplit=1)[1]
            for context in value.split(",")
        }

    parser.register("type", "CommaSeparatedKeyValues", _parse_context_values)

    parser.add_argument(
        "--version",
        help="Display version and exit",
        action="version",
        version=VERSION,
    )

    parser.add_argument(
        "--zimfarm-api-url",
        help=(
            "URL to the Zimfarm, including protocol and API version. "
            f"Defaults to {Context.zimfarm_api_url}"
        ),
    )

    parser.add_argument(
        "--zimfarm-username", help="Username to connect to the Zimfarm", required=True
    )

    parser.add_argument(
        "--zimfarm-password", help="Password to connect to the Zimfarm", required=True
    )

    parser.add_argument(
        "-p", "--push", action="store_true", help="Really apply changes"
    )

    parser.add_argument(
        "--values",
        type="CommaSeparatedKeyValues",
        help="CSV of key=value context variables, typically required to pass secrets",
    )

    parser.add_argument(
        "--overrides",
        type=Path,
        help=f"Path to the overrides.yaml file. Defaults to {Context.overrides}",
    )

    parser.add_argument("kind", choices=["ted", "devdocs", "freecodecamp"])

    args = parser.parse_args(raw_args)

    # Ignore unset values so they do not override the default specified in Context
    args_dict = {key: value for key, value in args._get_kwargs() if value}

    if "values" not in args_dict:
        args_dict["values"] = {}

    Context.setup(**args_dict)
