from marshmallow import Schema, fields, validate, validates_schema

from common.enum import DockerImageName, Offliner
from common.schemas import SerializableSchema
from common.schemas.fields import (
    validate_not_empty,
    validate_cpu,
    validate_memory,
    validate_disk,
    validate_lang_code,
    validate_schedule_name,
    validate_category,
    validate_warehouse_path,
    validate_offliner,
    validate_periodicity,
)
from common.schemas.offliners import (
    MWOfflinerFlagsSchema,
    YoutubeFlagsSchema,
    PhetFlagsSchema,
    GutenbergFlagsSchema,
    SotokiFlagsSchema,
)


class LanguageSchema(Schema):
    code = fields.String(required=True, validate=validate_lang_code)
    name_en = fields.String(required=True, validate=validate_not_empty)
    name_native = fields.String(required=True, validate=validate_not_empty)


class ResourcesSchema(Schema):
    cpu = fields.Integer(required=True, validate=validate_cpu)
    memory = fields.Integer(required=True, validate=validate_memory)
    disk = fields.Integer(required=True, validate=validate_disk)


class DockerImageSchema(Schema):
    name = fields.String(required=True, validate=validate.OneOf(DockerImageName.all()))
    tag = fields.String(required=True)

    # @validates_schema
    # def validate(self, data, **kwargs):
    #     if data["name"] == DockerImageName.mwoffliner:
    #         allowed_tags = {"1.9.9", "1.9.10", "latest"}
    #     else:
    #         allowed_tags = {"latest"}
    #     if data["tag"] not in allowed_tags:
    #         raise ValidationError(f'tag {data["tag"]} is not an allowed tag')


class ScheduleConfigSchema(SerializableSchema):

    task_name = fields.String(required=True, validate=validate_offliner)
    warehouse_path = fields.String(required=True, validate=validate_warehouse_path)
    image = fields.Nested(DockerImageSchema(), required=True)
    resources = fields.Nested(ResourcesSchema(), required=True)
    flags = fields.Dict(required=True)

    @staticmethod
    def get_offliner_schema(offliner):
        return {
            Offliner.mwoffliner: MWOfflinerFlagsSchema,
            Offliner.youtube: YoutubeFlagsSchema,
            Offliner.gutenberg: GutenbergFlagsSchema,
            Offliner.phet: PhetFlagsSchema,
            Offliner.sotoki: SotokiFlagsSchema,
        }.get(offliner, Schema)

    @validates_schema
    def validate(self, data, **kwargs):
        if "task_name" in data and "flag" in data:
            schema = self.get_offliner_schema(data["task_name"])
            data["flags"] = schema.load(data["flags"])


class ScheduleSchema(Schema):
    name = fields.String(required=True, validate=validate_schedule_name)
    language = fields.Nested(LanguageSchema(), required=True)
    category = fields.String(required=True, validate=validate_category)
    periodicity = fields.String(required=True, validate=validate_periodicity)
    tags = fields.List(
        fields.String(validate=validate_not_empty), required=True, default=[]
    )
    enabled = fields.Boolean(required=True, truthy=[True], falsy=[False])
    config = fields.Nested(ScheduleConfigSchema(), required=True)
