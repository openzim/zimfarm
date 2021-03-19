from common.schemas import SerializableSchema
from common.schemas.offliners.mwoffliner import MWOfflinerFlagsSchema
from common.schemas.offliners.youtube import YoutubeFlagsSchema
from common.schemas.offliners.sotoki import SotokiFlagsSchema
from common.schemas.offliners.nautilus import NautilusFlagsSchema
from common.schemas.offliners.ted import TedFlagsSchema
from common.schemas.offliners.openedx import OpenedxFlagsSchema
from common.schemas.offliners.gutenberg import GutenbergFlagsSchema
from common.schemas.offliners.zimit import ZimitFlagsSchema
from common.schemas.offliners.kolibri import KolibriFlagsSchema


class PhetFlagsSchema(SerializableSchema):
    class Meta:
        ordered = True
