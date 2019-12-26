from common.schemas import SerializableSchema
from common.schemas.offliners.mwoffliner import MWOfflinerFlagsSchema
from common.schemas.offliners.youtube import YoutubeFlagsSchema


class PhetFlagsSchema(SerializableSchema):
    class Meta:
        ordered = True


class GutenbergFlagsSchema(SerializableSchema):
    class Meta:
        ordered = True
