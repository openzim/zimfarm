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


class ConfigResourcesSchema(m.Schema):
    cpu = mf.Integer()
    disk = mf.Integer()
    memory = mf.Integer()


class ConfigWithOnlyTaskNameAndResourcesSchema(m.Schema):
    resources = mf.Nested(ConfigResourcesSchema)
    task_name = mf.String()


class TaskLightSchema(m.Schema):
    id = mf.String(data_key="_id")
    status = mf.String()
    timestamp = mf.Dict()
    schedule_name = mf.String()
    worker_name = mf.String(data_key="worker")
    updated_at = mf.DateTime()


class TaskFullSchema(TaskLightSchema):
    config = mf.Dict()
    events = mf.Dict()
    debug = mf.Dict()
    requested_by = mf.String()
    canceled_by = mf.String()
    container = mf.Dict()
    priority = mf.Integer()
    notification = mf.Dict()
    files = mf.Dict()
    upload = mf.Dict()


class RequestedTaskLightSchema(m.Schema):
    id = mf.String(data_key="_id")
    status = mf.String()
    config = mf.Nested(ConfigWithOnlyTaskNameAndResourcesSchema)
    timestamp = mf.Dict()
    requested_by = mf.String()
    priority = mf.Integer()
    schedule_name = mf.String()


class RequestedTaskFullSchema(RequestedTaskLightSchema):
    def get_worker_name(task: dbm.Task) -> str:
        if task.worker:
            return task.worker.name
        else:
            return None

    def get_schedule_name(task: dbm.Task) -> str:
        return task.schedule.name

    config = mf.Dict()  # override base
    events = mf.Dict()
    upload = mf.Dict()
    schedule_name = mf.Function(serialize=get_schedule_name)  # override base
    worker_name = mf.Function(serialize=get_worker_name)


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
