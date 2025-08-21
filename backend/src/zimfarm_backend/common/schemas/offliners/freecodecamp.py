from enum import StrEnum
from typing import Annotated, Literal

from pydantic import AnyUrl, Field, WrapValidator

from zimfarm_backend.common.schemas import DashModel
from zimfarm_backend.common.schemas.fields import (
    NotEmptyString,
    OptionalField,
    OptionalNotEmptyString,
    OptionalZIMFileName,
    OptionalZIMLongDescription,
    OptionalZIMOutputFolder,
    ZIMDescription,
    ZIMName,
    ZIMTitle,
    enum_member,
)


class FCCLanguage(StrEnum):
    """Language of zim file and curriculum"""

    ENGLISH = "eng"
    ESPANOL = "spa"
    GERMAN = "deu"
    ITALIAN = "ita"
    JAPANESE = "jpn"
    PORTOGUESE = "por"
    UKRAINIAN = "ukr"
    SWAHILI = "swa"
    # cmn = "chinese"
    # lzh = "chinese-traditional"


FCCLanguageValue = Annotated[FCCLanguage, WrapValidator(enum_member(FCCLanguage))]


class FreeCodeCampFlagsSchema(DashModel):
    offliner_id: Literal["freecodecamp"] = Field(alias="offliner_id")

    course: NotEmptyString = OptionalField(
        title="Course(s)",
        description="Course or course list (separated by commas)",
    )

    language: FCCLanguageValue = Field(
        title="Language", description="Language of zim file and curriculum."
    )

    name: ZIMName = Field(
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

    long_description: OptionalZIMLongDescription = OptionalField(
        title="Long description",
        description="Optional long description for your ZIM",
    )

    creator: OptionalNotEmptyString = OptionalField(
        title="Content Creator",
        description="Name of content creator. “freeCodeCamp” otherwise",
    )

    publisher: OptionalNotEmptyString = OptionalField(
        title="Publisher",
        description="Custom publisher name (ZIM metadata). “openZIM” otherwise",
    )

    debug: bool | None = OptionalField(
        title="Debug",
        description="Enable verbose output",
    )

    output: OptionalZIMOutputFolder = Field(
        title="Output folder",
        description="Output folder for ZIM file(s). Leave it as `/output`",
    )

    zim_file: OptionalZIMFileName = OptionalField(
        title="ZIM filename",
        description="ZIM file name (based on --name if not provided). "
        "Include {period} to insert date period dynamically",
    )

    illustration: AnyUrl | None = OptionalField(
        title="Illustration",
        description="URL for ZIM illustration. Freecodecamp default logo if missing",
    )
