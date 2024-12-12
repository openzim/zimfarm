import dataclasses
from pathlib import Path

from recipesauto.constants import ROOT_DIR


@dataclasses.dataclass(kw_only=True)
class Context:
    """Class holding every contextual / configuration bits which can be moved

    Used to easily pass information around in the scraper. One singleton instance is
    always available.
    """

    # singleton instance
    _instance: "Context | None" = None

    # push changes to Zimfarm
    push: bool = False

    # kind of recipes to maintain
    kind: str

    # URL to Zimfarm API
    zimfarm_api_url: str = "https://api.farm.openzim.org/v1"

    # Credentials to Zimfarm
    zimfarm_username: str
    zimfarm_password: str

    # timeout of HTTP calls
    http_timeout: int = 10

    # dict of values to use in configuration (typically to pass secrets)
    values: dict[str, str]

    # path to files with configuration override
    overrides: Path = Path(ROOT_DIR / "overrides.yaml")

    @classmethod
    def setup(cls, **kwargs):
        new_instance = cls(**kwargs)
        if cls._instance:
            # replace values 'in-place' so that we do not change the Context object
            # which might be already imported in some modules
            for field in dataclasses.fields(new_instance):
                cls._instance.__setattr__(
                    field.name, new_instance.__getattribute__(field.name)
                )
        else:
            cls._instance = new_instance

    @classmethod
    def get(cls) -> "Context":
        if not cls._instance:
            raise OSError("Uninitialized context")  # pragma: no cover
        return cls._instance
