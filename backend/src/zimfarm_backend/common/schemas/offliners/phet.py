# ruff: noqa: N815
from pydantic import Field

from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.common.schemas.fields import NotEmptyString


class PhetFlagsSchema(BaseModel):
    includeLanguages: NotEmptyString | None = Field(
        title="Include Languages",
        description="Spoken languages to ZIM, one ZIM per language and/or all in"
        " a `mul` ZIM.",
        default=None,
    )
    excludeLanguages: NotEmptyString | None = Field(
        title="Exclude Languages",
        description="Spoken languages to not ZIM.",
        default=None,
    )
    withoutLanguageVariants: bool = Field(
        title="Without Language Variants",
        description="Exclude languages with Country variant. For example `en_CA`"
        " will not be ZIMed with this argument.",
    )
    createMul: bool = Field(
        title="Create `mul` ZIM",
        description="Create a ZIM file with all languages (by default, scraper "
        "creates only one ZIM per language)",
    )
    mulOnly: bool = Field(
        title="Only `mul` ZIM",
        description="Create only `mul` ZIM, skip ZIM files for individual languages",
    )
