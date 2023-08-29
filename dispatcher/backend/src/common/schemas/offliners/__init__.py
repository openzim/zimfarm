from common.schemas import SerializableSchema
from common.schemas.offliners.freecodecamp import FreeCodeCampFlagsSchema
from common.schemas.offliners.gutenberg import GutenbergFlagsSchema
from common.schemas.offliners.ifixit import IFixitFlagsSchema
from common.schemas.offliners.kolibri import KolibriFlagsSchema
from common.schemas.offliners.mwoffliner import MWOfflinerFlagsSchema
from common.schemas.offliners.nautilus import NautilusFlagsSchema
from common.schemas.offliners.openedx import OpenedxFlagsSchema
from common.schemas.offliners.sotoki import SotokiFlagsSchema
from common.schemas.offliners.ted import TedFlagsSchema
from common.schemas.offliners.wikihow import WikihowFlagsSchema
from common.schemas.offliners.youtube import YoutubeFlagsSchema
from common.schemas.offliners.zimit import ZimitFlagsSchema

__all__ = (
    "FreeCodeCampFlagsSchema",
    "GutenbergFlagsSchema",
    "IFixitFlagsSchema",
    "KolibriFlagsSchema",
    "MWOfflinerFlagsSchema",
    "NautilusFlagsSchema",
    "OpenedxFlagsSchema",
    "SotokiFlagsSchema",
    "TedFlagsSchema",
    "WikihowFlagsSchema",
    "YoutubeFlagsSchema",
    "ZimitFlagsSchema",
)


class PhetFlagsSchema(SerializableSchema):
    class Meta:
        ordered = True
