import marshmallow as m
import marshmallow.fields as mf
from marshmallow_sqlalchemy import SQLAlchemySchema, auto_field

import db.models as dbm
from common.roles import get_role_for


class BaseSchema(SQLAlchemySchema):
    pass


class UserSchemaReadMany(BaseSchema):
    class Meta:
        model = dbm.User

    def get_role_from_user(user: dbm.User) -> str:
        return get_role_for(user.scope)

    username = auto_field()
    email = auto_field()
    role = mf.Function(serialize=get_role_from_user)


class SshKeyRead(BaseSchema):
    class Meta:
        model = dbm.Sshkey

    added = auto_field()
    fingerprint = auto_field()
    key = auto_field()
    last_used = auto_field()
    name = auto_field()
    pkcs8_key = auto_field()
    type = auto_field()


class UserSchemaReadOne(UserSchemaReadMany):
    scope = auto_field()
    ssh_keys = mf.List(mf.Nested(SshKeyRead))


class MostRecentTaskSchema(m.Schema):
    id = mf.String(data_key="_id")
    status = mf.String()
    updated_at = mf.DateTime()


class ConfigTaskOnlySchema(m.Schema):
    task_name = mf.String()


class LanguageSchema(m.Schema):
    code = mf.String()
    name_en = mf.String()
    name_native = mf.String()


class ScheduleLightSchema(m.Schema):
    name = mf.String()
    category = mf.String()
    most_recent_task = mf.Nested(MostRecentTaskSchema)
    config = mf.Nested(ConfigTaskOnlySchema)
    language = mf.Nested(LanguageSchema)


class ScheduleFullSchema(BaseSchema):
    class Meta:
        model = dbm.Schedule

    def get_language(schedule: dbm.Schedule):
        return {
            "code": schedule.language_code,
            "name_en": schedule.language_name_en,
            "name_native": schedule.language_name_native,
        }

    name = auto_field()
    category = auto_field()
    config = auto_field()
    enabled = auto_field()
    tags = auto_field()
    periodicity = auto_field()
    notification = auto_field()
    language = mf.Function(get_language)
