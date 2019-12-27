from common.schemas import SerializableSchema
from common.schemas.offliners.mwoffliner import MWOfflinerFlagsSchema
from common.schemas.offliners.youtube import YoutubeFlagsSchema
from common.schemas.offliners.sotoki import SotokiFlagsSchema


class PhetFlagsSchema(SerializableSchema):
    class Meta:
        ordered = True


class GutenbergFlagsSchema(SerializableSchema):
    class Meta:
        ordered = True
