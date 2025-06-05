from typing import Literal

from pydantic import Field

from zimfarm_backend.common.schemas import DashModel
from zimfarm_backend.common.schemas.fields import (
    OptionalField,
    OptionalNotEmptyString,
    OptionalZIMDescription,
    OptionalZIMLongDescription,
    OptionalZIMOutputFolder,
    OptionalZIMTitle,
)


class DevDocsFlagsSchema(DashModel):
    offliner_id: Literal["devdocs"] = Field(exclude=True)

    slug: OptionalNotEmptyString = OptionalField(
        title="Slug",
        description="""Fetch the provided Devdocs resource.
            Slugs are the first path entry in the Devdocs URL.
            For example, the slug for: `https://devdocs.io/gcc~12/` is `gcc~12`.
            Mutually exclusive with `All` setting, set only one option. Either this
            setting or `All` must be configured.""",
    )

    all_flag: bool | None = OptionalField(
        title="All",
        description="""Fetch all Devdocs resources, and produce one ZIM
        per resource. Mutually exclusive with `Slug` setting, set only
        one option. Either this setting or `Slug` must be configured.""",
        alias="all",
    )

    skip_slug_regex: OptionalNotEmptyString = OptionalField(
        title="Skip slugs regex",
        description="""Skips slugs matching the given regular expression.
        Do not set to fetch all slugs. Only useful when `All` is set.""",
    )

    file_name_format: OptionalNotEmptyString = OptionalField(
        title="ZIM filename",
        description="""ZIM filename. Do not input trailing `.zim`, it
        will be automatically added. You can use placeholders, see
        https://github.com/openzim/devdocs/blob/main/README.md. Defaults
        to devdocs.io_en_{clean_slug}_{period}""",
    )

    name_format: OptionalNotEmptyString = OptionalField(
        title="ZIM name",
        description="""ZIM name. You can use placeholders, see
        https://github.com/openzim/devdocs/blob/main/README.md. Defaults
        to devdocs.io_en_{clean_slug}""",
    )

    title_format: OptionalZIMTitle = OptionalField(
        title="ZIM title",
        description="""ZIM title. You can use placeholders, see
        https://github.com/openzim/devdocs/blob/main/README.md. Defaults
        to `{full_name} Docs`""",
    )

    description_format: OptionalZIMDescription = OptionalField(
        title="ZIM description",
        description="""ZIM description. You can use placeholders, see
        https://github.com/openzim/devdocs/blob/main/README.md. Defaults
        to `{full_name} docs by DevDocs`""",
    )

    long_description_format: OptionalZIMLongDescription = OptionalField(
        title="ZIM long description",
        description="""ZIM long description. You can use placeholders, see
        https://github.com/openzim/devdocs/blob/main/README.md. Defaults to no
        long description""",
    )

    logo_format: OptionalNotEmptyString = OptionalField(
        title="ZIM illustration",
        description="""URL to a custom ZIM logo in PNG, JPG, or SVG format. You
        can use placeholders, see https://github.com/openzim/devdocs/blob/main/README.md.""",
    )

    tags: OptionalNotEmptyString = OptionalField(
        title="ZIM Tags",
        description="""List of semi-colon-separated Tags for the ZIM file.
        You can use placeholders, see https://github.com/openzim/devdocs/blob/main/README.md.
        Defaults to `devdocs;{slug_without_version}`""",
    )

    creator: OptionalNotEmptyString = OptionalField(
        title="Creator",
        description="""Name of content creator. “DevDocs” otherwise""",
    )

    publisher: OptionalNotEmptyString = OptionalField(
        title="Publisher",
        description="""Custom publisher name (ZIM metadata). “openZIM” otherwise""",
    )

    output: OptionalZIMOutputFolder = OptionalField(
        title="Output folder",
        description="""Output folder for ZIM file(s). Leave it as `/output`""",
    )

    debug: bool | None = OptionalField(
        title="Debug",
        description="""Enable verbose output""",
    )
