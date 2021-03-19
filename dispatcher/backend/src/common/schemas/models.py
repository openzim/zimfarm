import re

from marshmallow import Schema, fields, validate, validates_schema, pre_load

from common.enum import DockerImageName, Offliner, Platform
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
    validate_platform,
    validate_platform_value,
    validate_slack_target,
)
from common.schemas.offliners import (
    MWOfflinerFlagsSchema,
    YoutubeFlagsSchema,
    PhetFlagsSchema,
    GutenbergFlagsSchema,
    SotokiFlagsSchema,
    NautilusFlagsSchema,
    TedFlagsSchema,
    OpenedxFlagsSchema,
    ZimitFlagsSchema,
    KolibriFlagsSchema,
)


class LanguageSchema(Schema):
    code = fields.String(required=True, validate=validate_lang_code)
    name_en = fields.String(required=True, validate=validate_not_empty)
    name_native = fields.String(required=True, validate=validate_not_empty)


class ResourcesSchema(Schema):
    cpu = fields.Integer(required=True, validate=validate_cpu)
    memory = fields.Integer(required=True, validate=validate_memory)
    disk = fields.Integer(required=True, validate=validate_disk)
    shm = fields.Integer(required=False, validate=validate_memory)
    cap_add = fields.List(fields.String(), required=False)
    cap_drop = fields.List(fields.String(), required=False)


class DockerImageSchema(Schema):
    name = fields.String(required=True, validate=validate.OneOf(DockerImageName.all()))
    tag = fields.String(required=True)

    @pre_load
    def strip_prefix(self, in_data, **kwargs):
        # strip the image prefix out so we don't have to care about it later-on
        # should ideally be dynamic but this is based on the offliner/task_name
        # which we don't have access to here. awaiting additional registry usage to fix
        in_data["name"] = re.sub(r"^ghcr.io/", "", in_data["name"])
        return in_data


class ScheduleConfigSchema(SerializableSchema):

    task_name = fields.String(required=True, validate=validate_offliner)
    warehouse_path = fields.String(required=True, validate=validate_warehouse_path)
    image = fields.Nested(DockerImageSchema(), required=True)
    resources = fields.Nested(ResourcesSchema(), required=True)
    flags = fields.Dict(required=True)
    platform = fields.String(required=True, allow_none=True, validate=validate_platform)

    @staticmethod
    def get_offliner_schema(offliner):
        return {
            Offliner.mwoffliner: MWOfflinerFlagsSchema,
            Offliner.youtube: YoutubeFlagsSchema,
            Offliner.gutenberg: GutenbergFlagsSchema,
            Offliner.phet: PhetFlagsSchema,
            Offliner.sotoki: SotokiFlagsSchema,
            Offliner.nautilus: NautilusFlagsSchema,
            Offliner.ted: TedFlagsSchema,
            Offliner.openedx: OpenedxFlagsSchema,
            Offliner.zimit: ZimitFlagsSchema,
            Offliner.kolibri: KolibriFlagsSchema,
        }.get(offliner, Schema)

    @validates_schema
    def validate(self, data, **kwargs):
        if "task_name" in data and "flag" in data:
            schema = self.get_offliner_schema(data["task_name"])
            data["flags"] = schema.load(data["flags"])


class EventNotificationSchema(SerializableSchema):
    mailgun = fields.List(fields.Email(), required=False)
    webhook = fields.List(fields.Url(), required=False)
    slack = fields.List(fields.String(validate=validate_slack_target), required=False)


class ScheduleNotificationSchema(SerializableSchema):
    requested = fields.Nested(EventNotificationSchema(), required=False)
    started = fields.Nested(EventNotificationSchema(), required=False)
    ended = fields.Nested(EventNotificationSchema(), required=False)


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
    notification = fields.Nested(
        ScheduleNotificationSchema(), required=False, default={}, missing={}
    )


PlatformsLimitSchema = Schema.from_dict(
    {
        platform: fields.Integer(required=False, validate=validate_platform_value)
        for platform in Platform.all()
    }
)
