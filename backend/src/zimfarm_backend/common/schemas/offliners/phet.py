from marshmallow import fields

from common.schemas import SerializableSchema, String


class PhetFlagsSchema(SerializableSchema):
    class Meta:
        ordered = True

    includeLanguages = String(
        required=False,
        metadata={
            "label": "Include Languages",
            "description": "Spoken languages to ZIM, one ZIM per language and/or all in"
            " a `mul` ZIM.",
        },
    )
    excludeLanguages = String(
        required=False,
        metadata={
            "label": "Exclude Languages",
            "description": "Spoken languages to not ZIM.",
        },
    )
    withoutLanguageVariants = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={
            "label": "Without Language Variants",
            "description": "Exclude languages with Country variant. For example `en_CA`"
            " will not be ZIMed with this argument.",
        },
    )
    createMul = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={
            "label": "Create `mul` ZIM",
            "description": "Create a ZIM file with all languages (by default, scraper "
            "creates only one ZIM per language)",
        },
    )
    mulOnly = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={
            "label": "Only `mul` ZIM",
            "description": "Create only `mul` ZIM, skip ZIM files for individual "
            "languages",
        },
    )
