from marshmallow import fields

from common.schemas import SerializableSchema, String
from common.schemas.fields import (
    validate_output,
    validate_zim_description,
    validate_zim_longdescription,
)


class DevDocsFlagsSchema(SerializableSchema):
    class Meta:
        ordered = True

    slug = String(
        metadata={
            "label": "Slug",
            "description": "Fetch the provided Devdocs resource. "
            "Slugs are the first path entry in the Devdocs URL. "
            "For example, the slug for: `https://devdocs.io/gcc~12/` is `gcc~12`. "
            "Mutually exclusive with `All` setting, set only one option. Either this"
            "setting or `All` must be configured.",
        },
    )

    all_flag = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={
            "label": "All",
            "description": "Fetch all Devdocs resources, and produce one ZIM "
            "per resource. Mutually exclusive with `Slug` setting, set only "
            "one option. Either this setting or `Slug` must be configured.",
        },
        data_key="all",
    )

    skip_slug_regex = String(
        metadata={
            "label": "Skip slugs regex",
            "description": "Skips slugs matching the given regular expression."
            "Do not set to fetch all slugs. Only useful when `All` is set.",
        },
        data_key="skip-slug-regex",
    )

    file_name_format = String(
        metadata={
            "label": "ZIM filename",
            "description": "ZIM filename. Do not input trailing `.zim`, it "
            "will be automatically added. You can use placeholders, see "
            "https://github.com/openzim/devdocs/blob/main/README.md. Defaults "
            "to devdocs.io_en_{clean_slug}_{period}",
        },
        data_key="file-name-format",
    )

    name_format = String(
        metadata={
            "label": "ZIM name",
            "description": "ZIM name. You can use placeholders, see "
            "https://github.com/openzim/devdocs/blob/main/README.md. Defaults "
            "to devdocs.io_en_{clean_slug}",
        },
        data_key="name-format",
    )

    title_format = String(
        metadata={
            "label": "ZIM title",
            "description": "ZIM title. You can use placeholders, see "
            "https://github.com/openzim/devdocs/blob/main/README.md. Defaults "
            "to `{full_name} Docs`",
        },
        data_key="title-format",
    )

    description_format = String(
        metadata={
            "label": "ZIM description",
            "description": "ZIM description. You can use placeholders, see "
            "https://github.com/openzim/devdocs/blob/main/README.md. Defaults "
            "to `{full_name} docs by DevDocs`",
        },
        data_key="description-format",
        validate=validate_zim_description,
    )

    long_description_format = String(
        metadata={
            "label": "ZIM long description",
            "description": "ZIM long description. You can use placeholders, see "
            "https://github.com/openzim/devdocs/blob/main/README.md. Defaults to no "
            "long description",
        },
        data_key="long-description-format",
        validate=validate_zim_longdescription,
    )

    tags = String(
        metadata={
            "label": "ZIM Tags",
            "description": "List of semi-colon-separated Tags for the ZIM file. "
            " You can use placeholders, see "
            "https://github.com/openzim/devdocs/blob/main/README.md. Defaults to"
            "`devdocs;{slug_without_version}`",
        }
    )

    creator = String(
        metadata={
            "label": "Creator",
            "description": "Name of content creator. “DevDocs” otherwise",
        },
    )

    publisher = String(
        metadata={
            "label": "Publisher",
            "description": "Custom publisher name (ZIM metadata). “openZIM” otherwise",
        },
    )

    output = String(
        metadata={
            "label": "Output folder",
            "placeholder": "/output",
            "description": "Output folder for ZIM file(s). Leave it as `/output`",
        },
        load_default="/output",
        dump_default="/output",
        validate=validate_output,
    )

    debug = fields.Boolean(
        truthy=[True],
        falsy=[False],
        metadata={"label": "Debug", "description": "Enable verbose output"},
    )
