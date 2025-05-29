import datetime
from typing import Annotated, Any

import pytz
from pydantic import AfterValidator, BaseModel, Field, computed_field

from zimfarm_backend.common.roles import get_role_for


def make_datetime_aware(dt: datetime.datetime) -> datetime.datetime:
    """Make the datetime localized so that it is serialized with a trailing 'Z'"""
    if dt.tzinfo is None:
        return pytz.utc.localize(dt)
    return dt


MadeAwareDateTime = Annotated[datetime.datetime, AfterValidator(make_datetime_aware)]


class UserSchemaReadMany(BaseModel):
    """
    Schema for reading a user model
    """

    username: str
    email: str | None
    scope: dict[str, Any] | None = None

    @computed_field
    @property
    def role(self) -> str:
        if self.scope is None:
            return "custom"
        return get_role_for(self.scope)


class SshKeyRead(BaseModel):
    """
    Schema for reading a ssh key model
    """

    added: datetime.datetime
    fingerprint: str
    key: str
    name: str
    pkcs8_key: str
    type: str


class UserSchemaReadOne(UserSchemaReadMany):
    """
    Schema for reading a user model with its ssh keys
    """

    ssh_keys: list[SshKeyRead]


class ConfigResourcesSchema(BaseModel):
    """
    Schema for reading a config's resources
    """

    cpu: int
    disk: int
    memory: int


class ConfigWithOnlyResourcesSchema(BaseModel):
    """
    Schema for reading a config model with only its resources
    """

    resources: ConfigResourcesSchema


class ConfigWithOnlyTaskNameAndResourcesSchema(ConfigWithOnlyResourcesSchema):
    """
    Schema for reading a config model with only its task name and resources
    """

    task_name: str


class TaskLightSchema(BaseModel):
    """
    Schema for reading a task model with some fields
    """

    id: str = Field(alias="_id")
    status: str
    timestamp: dict[str, Any]
    schedule_name: str
    worker_name: str = Field(alias="worker")
    updated_at: datetime.datetime
    config: ConfigWithOnlyResourcesSchema
    original_schedule_name: str


class TaskFullSchema(TaskLightSchema):
    """
    Schema for reading a task model with all fields
    """

    events: list[dict[str, Any]]
    debug: dict[str, Any]
    requested_by: str
    canceled_by: str | None
    container: dict[str, Any]
    priority: int
    notification: dict[str, Any]
    files: dict[str, Any]
    upload: dict[str, Any]


class NameOnlySchema(BaseModel):
    """
    Schema for reading only a name field from a model
    """

    name: str


class ScheduleAwareTaskFullSchema(TaskFullSchema):
    """
    Schema for reading a task model with all fields and its schedule name
    """

    schedule: NameOnlySchema


class RequestedTaskLightSchema(BaseModel):
    """
    Schema for reading a requested task model with some fields
    """

    id: str = Field(alias="_id")
    status: str
    config: ConfigWithOnlyTaskNameAndResourcesSchema
    timestamp: dict[str, Any]
    requested_by: str
    priority: int
    schedule_name: str
    original_schedule_name: str
    worker: NameOnlySchema


class RequestedTaskFullSchema(RequestedTaskLightSchema):
    """
    Schema for reading a requested task model with all fields
    """

    events: list[dict[str, Any]]
    upload: dict[str, Any]
    notification: dict[str, Any]
    rank: int
    schedule: NameOnlySchema


class MostRecentTaskSchema(BaseModel):
    """
    Schema for reading a most recent task model with some fields
    """

    id: str = Field(alias="_id")
    status: str
    updated_at = MadeAwareDateTime


class ConfigTaskOnlySchema(BaseModel):
    """
    Schema for reading a config model with only its task name
    """

    task_name: str


class LanguageSchema(BaseModel):
    """
    Schema for reading a language model
    """

    code: str
    name_en: str
    name_native: str


class ScheduleLightSchema(BaseModel):
    """
    Schema for reading a schedule model with some fields
    """

    name: str
    category: str
    most_recent_task: MostRecentTaskSchema
    config: ConfigTaskOnlySchema
    language: LanguageSchema
    enabled: bool
    count_requested_task: int

    @computed_field
    @property
    def is_requested(self) -> bool:
        return self.count_requested_task > 0


class ScheduleDurationSchema(BaseModel):
    """
    Schema for reading a schedule duration model
    """

    value: int
    on: str
    worker: NameOnlySchema | None
    default: bool


class ScheduleFullSchema(BaseModel):
    """
    Schema for reading a schedule model with all fields
    """

    language_code: str
    language_name_en: str
    language_name_native: str
    durations: list[ScheduleDurationSchema]
    name: str
    category: str
    config: dict[str, Any]
    enabled: bool
    tags: list[str]
    periodicity: str
    notification: dict[str, Any]
    most_recent_task: MostRecentTaskSchema
    count_requested_task: int

    @computed_field
    @property
    def is_requested(self) -> bool:
        return self.count_requested_task > 0

    @computed_field
    @property
    def language(self) -> LanguageSchema:
        return LanguageSchema(
            code=self.language_code,
            name_en=self.language_name_en,
            name_native=self.language_name_native,
        )

    @computed_field
    def get_duration(self) -> dict[str, Any]:
        duration_res: dict[str, Any] = {}
        duration_res["available"] = False
        duration_res["default"] = {}
        duration_res["workers"] = {}
        for duration in self.durations:
            if duration.default:
                duration_res["default"] = ScheduleDurationSchema.model_validate(
                    duration
                ).model_dump(mode="json")
            if duration.worker:
                duration_res["available"] = True
                duration_res["workers"][duration.worker.name] = (
                    ScheduleDurationSchema.model_validate(duration).model_dump(
                        mode="json"
                    )
                )
        return duration_res
