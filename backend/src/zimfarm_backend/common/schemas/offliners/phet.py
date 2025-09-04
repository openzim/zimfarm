# ruff: noqa: N815
# from typing import Literal
#
# from pydantic import Field
#
# from zimfarm_backend.common.schemas import DashModel
# from zimfarm_backend.common.schemas.fields import (
#         OptionalField,
#         OptionalNotEmptyString,
# )
#
#
# class PhetFlagsSchema(DashModel):
#     offliner_id: Literal["phet"] = Field(alias="offliner_id")
#
#     includeLanguages: OptionalNotEmptyString = OptionalField(
#         title="Include Languages",
#         description="Spoken languages to ZIM, one ZIM per language and/or all in"
#         " a `mul` ZIM.",
#     )
#     excludeLanguages: OptionalNotEmptyString = OptionalField(
#         title="Exclude Languages",
#         description="Spoken languages to not ZIM.",
#     )
#     withoutLanguageVariants: bool | None = OptionalField(
#         title="Without Language Variants",
#         description="Exclude languages with Country variant. For example `en_CA`"
#         " will not be ZIMed with this argument.",
#     )
#     createMul: bool | None = OptionalField(
#         title="Create `mul` ZIM",
#         description="Create a ZIM file with all languages (by default, scraper "
#         "creates only one ZIM per language)",
#     )
#     mulOnly: bool | None = OptionalField(
#         title="Only `mul` ZIM",
#         description="Create only `mul` ZIM, skip ZIM files for individual languages",
#     )

import json

from zimfarm_backend.common.constants import OFFLINER_DATA_PATH
from zimfarm_backend.common.schemas import DashModel
from zimfarm_backend.common.schemas.offliners.builder import (
    OfflinerFlagSchema,
    build_offliner_model,
)

flags = json.loads((OFFLINER_DATA_PATH / "phet.json").read_text())

PhetFlagsSchema = build_offliner_model(
    model_name="PhetFlagsSchema",
    offliner_id="phet",
    schema=OfflinerFlagSchema.model_validate({"flags": flags}),
    base_model_cls=DashModel,
)
