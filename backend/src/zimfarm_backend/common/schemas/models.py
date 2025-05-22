import re

from marshmallow import Schema, fields, pre_load, validate, validates_schema

from zimfarm_backend.common import constants
from zimfarm_backend.common.enum import DockerImageName, Offliner, Platform
from zimfarm_backend.common.schemas import SerializableSchema, String
from zimfarm_backend.common.schemas.fields import (
    validate_category,
    validate_cpu,
    validate_disk,
    validate_lang_code,
    validate_memory,
    validate_not_empty,
    validate_offliner,
    validate_periodicity,
    validate_platform,
    validate_platform_value,
    validate_schedule_name,
    validate_slack_target,
    validate_warehouse_path,
)
from zimfarm_backend.common.schemas.offliners import (
    DevDocsFlagsSchema,
    FreeCodeCampFlagsSchema,
    GutenbergFlagsSchema,
    IFixitFlagsSchema,
    KolibriFlagsSchema,
    MindtouchFlagsSchema,
    MWOfflinerFlagsSchema,
    NautilusFlagsSchema,
    NautilusFlagsSchemaRelaxed,
    OpenedxFlagsSchema,
    PhetFlagsSchema,
    SotokiFlagsSchema,
    TedFlagsSchema,
    WikihowFlagsSchema,
    YoutubeFlagsSchema,
    ZimitFlagsSchema,
    ZimitFlagsSchemaRelaxed,
)


class LanguageSchema(Schema):
    code = String(required=True, validate=validate_lang_code)
    name_en = String(required=True, validate=validate_not_empty)
    name_native = String(required=True, validate=validate_not_empty)


class ResourcesSchema(Schema):
    cpu = fields.Integer(required=True, validate=validate_cpu)
    memory = fields.Integer(required=True, validate=validate_memory)
    disk = fields.Integer(required=True, validate=validate_disk)
    shm = fields.Integer(required=False, validate=validate_memory)
    cap_add = fields.List(String(), required=False)
    cap_drop = fields.List(String(), required=False)


class DockerImageSchema(Schema):
    name = String(required=True, validate=validate.OneOf(DockerImageName.all()))
    tag = String(required=True)

    @pre_load
    def strip_prefix(self, in_data, **kwargs):
        # strip the image prefix out so we don't have to care about it later-on
        # should ideally be dynamic but this is based on the offliner/task_name
        # which we don't have access to here. awaiting additional registry usage to fix
        in_data["name"] = re.sub(r"^ghcr.io/", "", in_data["name"])
        return in_data


class ScheduleConfigSchema(SerializableSchema):
    task_name = String(required=True, validate=validate_offliner)
    warehouse_path = String(required=True, validate=validate_warehouse_path)
    image = fields.Nested(DockerImageSchema(), required=True)
    resources = fields.Nested(ResourcesSchema(), required=True)
    flags = fields.Dict(required=True)
    platform = String(required=True, allow_none=True, validate=validate_platform)
    artifacts_globs = fields.List(String(validate=validate_not_empty), required=False)
    monitor = fields.Boolean(required=True, truthy=[True], falsy=[False])

    @staticmethod
    def get_offliner_schema(offliner):
        return {
            Offliner.mwoffliner: MWOfflinerFlagsSchema,
            Offliner.youtube: YoutubeFlagsSchema,
            Offliner.gutenberg: GutenbergFlagsSchema,
            Offliner.phet: PhetFlagsSchema,
            Offliner.sotoki: SotokiFlagsSchema,
            Offliner.nautilus: (
                NautilusFlagsSchemaRelaxed
                if constants.NAUTILUS_USE_RELAXED_SCHEMA
                else NautilusFlagsSchema
            ),
            Offliner.ted: TedFlagsSchema,
            Offliner.openedx: OpenedxFlagsSchema,
            Offliner.zimit: (
                ZimitFlagsSchemaRelaxed
                if constants.ZIMIT_USE_RELAXED_SCHEMA
                else ZimitFlagsSchema
            ),
            Offliner.kolibri: KolibriFlagsSchema,
            Offliner.wikihow: WikihowFlagsSchema,
            Offliner.ifixit: IFixitFlagsSchema,
            Offliner.freecodecamp: FreeCodeCampFlagsSchema,
            Offliner.devdocs: DevDocsFlagsSchema,
            Offliner.mindtouch: MindtouchFlagsSchema,
        }.get(offliner, Schema)

    @validates_schema
    def validate(self, data, **kwargs):
        if "task_name" in data and "flag" in data:
            schema = self.get_offliner_schema(data["task_name"])
            data["flags"] = schema.load(data["flags"])


class EventNotificationSchema(SerializableSchema):
    mailgun = fields.List(fields.Email(), required=False)
    webhook = fields.List(fields.Url(require_tld=False), required=False)
    slack = fields.List(String(validate=validate_slack_target), required=False)


class ScheduleNotificationSchema(SerializableSchema):
    requested = fields.Nested(EventNotificationSchema(), required=False)
    started = fields.Nested(EventNotificationSchema(), required=False)
    ended = fields.Nested(EventNotificationSchema(), required=False)


class ScheduleSchema(Schema):
    name = String(required=True, validate=validate_schedule_name)
    language = fields.Nested(LanguageSchema(), required=True)
    category = String(required=True, validate=validate_category)
    periodicity = String(required=True, validate=validate_periodicity)
    tags = fields.List(
        String(validate=validate_not_empty), required=True, dump_default=[]
    )
    enabled = fields.Boolean(required=True, truthy=[True], falsy=[False])
    config = fields.Nested(ScheduleConfigSchema(), required=True)
    notification = fields.Nested(
        ScheduleNotificationSchema(), required=False, dump_default={}, load_default={}
    )


PlatformsLimitSchema = Schema.from_dict(
    {
        platform: fields.Integer(required=False, validate=validate_platform_value)
        for platform in Platform.all()
    }
)
