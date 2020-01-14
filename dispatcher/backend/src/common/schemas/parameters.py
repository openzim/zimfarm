from marshmallow import fields, Schema

from common.schemas.fields import (
    skip_field,
    limit_field_20_200,
    limit_field_20_500,
    worker_field,
    priority_field,
    schedule_name_field,
    offliner_field,
    category_field,
    periodicity_field,
    tag_field,
    username_field,
    email_field,
    validate_cpu,
    validate_memory,
    validate_disk,
    validate_priority,
    validate_not_empty,
    validate_schedule_name,
    validate_role,
    validate_warehouse_path,
    validate_status,
    validate_event,
    validate_worker_name,
)
from common.schemas.models import LanguageSchema, DockerImageSchema, ResourcesSchema

# languages GET
class SkipLimit500Schema(Schema):
    skip = skip_field
    limit = limit_field_20_500


# tags GET, # users GET, # workers GET
class SkipLimitSchema(Schema):
    skip = skip_field
    limit = limit_field_20_200


# requested-tasks
class RequestedTaskSchema(Schema):
    skip = skip_field
    limit = limit_field_20_200

    worker = worker_field
    priority = priority_field
    schedule_name = schedule_name_field

    matching_cpu = fields.Integer(required=False, validate=validate_cpu)
    matching_memory = fields.Integer(required=False, validate=validate_memory)
    matching_disk = fields.Integer(required=False, validate=validate_disk)
    matching_offliners = fields.List(offliner_field, required=False)


# requested-tasks for worker
class WorkerRequestedTaskSchema(Schema):
    worker = fields.String(required=True, validate=validate_worker_name)
    avail_cpu = fields.Integer(required=True, validate=validate_cpu)
    avail_memory = fields.Integer(required=True, validate=validate_memory)
    avail_disk = fields.Integer(required=True, validate=validate_disk)


# requested-tasks POST
class NewRequestedTaskSchema(Schema):
    schedule_names = fields.List(schedule_name_field, required=True)
    priority = priority_field
    worker = worker_field


# requested-tasks PATCH
class UpdateRequestedTaskSchema(Schema):
    priority = fields.Integer(required=True, validate=validate_priority)


# schedule GET
class SchedulesSchema(Schema):
    skip = skip_field
    limit = limit_field_20_200
    category = fields.List(category_field, required=False)
    tag = tag_field
    lang = fields.List(fields.String(validate=validate_not_empty), required=False)
    name = schedule_name_field


# schedule PATCH
class UpdateSchema(Schema):
    name = schedule_name_field
    language = fields.Nested(LanguageSchema(), required=False)
    category = category_field
    periodicity = periodicity_field
    tags = tag_field
    enabled = fields.Boolean(required=False, truthy={True}, falsy={False})
    task_name = offliner_field
    warehouse_path = fields.String(required=False, validate=validate_warehouse_path)
    image = fields.Nested(DockerImageSchema, required=False)
    resources = fields.Nested(ResourcesSchema, required=False)
    flags = fields.Dict(required=False)


# schedule clone
class CloneSchema(Schema):
    name = fields.String(required=True, validate=validate_schedule_name)


# tasks GET
class TasksSchema(Schema):
    skip = skip_field
    limit = limit_field_20_200
    status = fields.List(fields.String(validate=validate_status), required=False)
    schedule_name = schedule_name_field


# tasks POST
class TaskCreateSchema(Schema):
    worker_name = fields.String(required=True, validate=validate_worker_name)


# tasks PATCH
class TasKUpdateSchema(Schema):
    event = fields.String(required=True, validate=validate_event)
    payload = fields.Dict(required=True)


# users keys POST
class KeySchema(Schema):
    name = fields.String(required=True, validate=validate_not_empty)
    key = fields.String(required=True, validate=validate_not_empty)


# users POST
class UserCreateSchema(Schema):
    username = username_field
    password = fields.String(required=True, validate=validate_not_empty)
    email = email_field
    role = fields.String(required=True, validate=validate_role)


# users PATCH
class UserUpdateSchema(Schema):
    email = email_field
    role = fields.String(required=False, validate=validate_role)


# workers checkin
class WorkerCheckInSchema(Schema):
    username = username_field
    cpu = fields.Integer(required=True, validate=validate_cpu)
    memory = fields.Integer(required=True, validate=validate_memory)
    disk = fields.Integer(required=True, validate=validate_disk)
    offliners = fields.List(offliner_field, required=True)
