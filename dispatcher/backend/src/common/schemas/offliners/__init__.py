from common.schemas import SerializableSchema
from common.schemas.offliners.mwoffliner import MWOfflinerFlagsSchema
from common.schemas.offliners.youtube import YoutubeFlagsSchema
from common.schemas.offliners.sotoki import SotokiFlagsSchema
from common.schemas.offliners.nautilus import NautilusFlagsSchema
from common.schemas.offliners.ted import TedFlagsSchema
from common.schemas.offliners.gutenberg import GutenbergFlagsSchema


class PhetFlagsSchema(SerializableSchema):
    class Meta:
        ordered = True

