from typing import Optional, Union

import marshmallow as m
import marshmallow.fields as mf
import pytz
from marshmallow_sqlalchemy import SQLAlchemySchema, auto_field

import db.models as dbm
from common.roles import get_role_for


class MadeAwareDateTime(mf.DateTime):
    def _serialize(self, unaware, attr, obj, **kwargs) -> Optional[Union[str, float]]:
        """Make the datetime localized so that it is serialized with a trailing 'Z'"""
        if not unaware:
            return None
        aware = pytz.utc.localize(unaware)
        return super()._serialize(aware, attr, obj, **kwargs)


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
    updated_at = MadeAwareDateTime()
    config = mf.Nested(ConfigWithOnlyTaskNameAndResourcesSchema, only=["resources"])
    original_schedule_name = mf.String()


class TaskFullSchema(TaskLightSchema):
    config = mf.Dict()
    events = mf.List(mf.Dict)
    debug = mf.Dict()
    requested_by = mf.String()
    canceled_by = mf.String()
    container = mf.Dict()
    priority = mf.Integer()
    notification = mf.Dict()
    files = mf.Dict()
    upload = mf.Dict()


class ScheduleAwareTaskFullSchema(TaskFullSchema):
    def get_schedule_name(task: dbm.Task) -> str:
        return getattr(task.schedule, "name", "none")

    schedule_name = mf.Function(serialize=get_schedule_name)  # override base


class RequestedTaskLightSchema(m.Schema):
    id = mf.String(data_key="_id")
    status = mf.String()
    config = mf.Nested(ConfigWithOnlyTaskNameAndResourcesSchema)
    timestamp = mf.Dict()
    requested_by = mf.String()
    priority = mf.Integer()
    schedule_name = mf.String()
    original_schedule_name = mf.String()
    worker = mf.String()


class RequestedTaskFullSchema(RequestedTaskLightSchema):
    def get_worker_name(task: dbm.Task) -> str:
        if task.worker:
            return task.worker.name
        else:
            return None

    def get_schedule_name(task: dbm.Task) -> str:
        return getattr(task.schedule, "name", "none")

    config = mf.Dict()  # override base
    events = mf.List(mf.Dict)
    upload = mf.Dict()
    schedule_name = mf.Function(serialize=get_schedule_name)  # override base
    worker = mf.Function(serialize=get_worker_name)


class MostRecentTaskSchema(m.Schema):
    id = mf.String(data_key="_id")
    status = mf.String()
    updated_at = MadeAwareDateTime()


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

    def get_one_duration(duration: dbm.ScheduleDuration):
        one_duration_res = {}
        one_duration_res["value"] = duration.value
        one_duration_res["on"] = duration.on
        if duration.worker:
            one_duration_res["worker"] = duration.worker.name
        return one_duration_res

    def get_duration(schedule: dbm.Schedule):
        duration_res = {}
        duration_res["available"] = False
        duration_res["default"] = {}
        duration_res["workers"] = {}
        for duration in schedule.durations:
            if duration.default:
                duration_res["default"] = ScheduleFullSchema.get_one_duration(duration)
            if duration.worker:
                duration_res["available"] = True
                duration_res["workers"][
                    duration.worker.name
                ] = ScheduleFullSchema.get_one_duration(duration)
        return duration_res

    name = auto_field()
    category = auto_field()
    config = auto_field()
    enabled = auto_field()
    tags = auto_field()
    periodicity = auto_field()
    notification = auto_field()
    language = mf.Function(get_language)
    most_recent_task = mf.Nested(MostRecentTaskSchema)
    duration = mf.Function(get_duration)
