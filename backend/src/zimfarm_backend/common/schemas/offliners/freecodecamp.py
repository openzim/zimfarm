from enum import StrEnum

from pydantic import Field
from pydantic.types import AnyUrl

from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.common.schemas.fields import (
    NotEmptyString,
    ZIMDescription,
    ZIMFileName,
    ZIMLongDescription,
    ZIMOutputFolder,
    ZIMTitle,
)


class FCCLanguage(StrEnum):
    """Language of zim file and curriculum. One of"""

    eng = "english"
    spa = "espanol"
    deu = "german"
    ita = "italian"
    jpn = "japanese"
    por = "portuguese"
    ukr = "ukrainian"
    swa = "swahili"
    # cmn = "chinese"
    # lzh = "chinese-traditional"


class FreeCodeCampFlagsSchema(BaseModel):
    course: NotEmptyString = Field(
        title="Course(s)",
        description="Course or course list (separated by commas)",
    )

    language: FCCLanguage = Field(
        title="Language",
        description="Language of zim file and curriculum. One of "
        + ", ".join(
            [f"'{language.name}' ({language.value})" for language in FCCLanguage]
        )
        + ".",
    )

    name: NotEmptyString = Field(
        title="Name",
        description="ZIM name",
    )

    title: ZIMTitle = Field(
        title="Title",
        description="ZIM title",
    )

    description: ZIMDescription = Field(
        title="Description",
        description="Description for your ZIM",
    )

    long_description: ZIMLongDescription = Field(
        title="Long description",
        description="Optional long description for your ZIM",
        alias="long-description",
    )

    creator: NotEmptyString = Field(
        title="Content Creator",
        description="Name of content creator. “freeCodeCamp” otherwise",
        default="freeCodeCamp",
    )

    publisher: NotEmptyString = Field(
        title="Publisher",
        description="Custom publisher name (ZIM metadata). “openZIM” otherwise",
        default="openZIM",
    )

    debug: bool = Field(
        title="Debug",
        description="Enable verbose output",
    )

    output: ZIMOutputFolder = Field(
        title="Output folder",
        description="Output folder for ZIM file(s). Leave it as `/output`",
        default="/output",
        validate_default=True,
    )

    zim_file: ZIMFileName = Field(
        title="ZIM filename",
        description="ZIM file name (based on --name if not provided). "
        "Include {period} to insert date period dynamically",
    )

    illustration: AnyUrl | None = Field(
        title="Illustration",
        description="URL for ZIM illustration. Freecodecamp default logo if missing",
        default=None,
    )
