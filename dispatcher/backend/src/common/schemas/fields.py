from marshmallow import fields, validate

from common.roles import ROLES
from common.enum import Offliner, ScheduleCategory, TaskStatus, SchedulePeriodicity

# validators
validate_priority = validate.Range(min=0, max=10)
validate_schedule_name = validate.Length(min=2)
validate_not_empty = validate.Length(min=1)
validate_role = validate.OneOf(ROLES.keys())
validate_cpu = validate.Range(min=0)
validate_memory = validate.Range(min=0)
validate_disk = validate.Range(min=0)
validate_lang_code = validate.Length(min=2, max=3)
validate_output = validate.Equal("/output")
validate_category = validate.OneOf(ScheduleCategory.all())
validate_warehouse_path = validate.OneOf(ScheduleCategory.all_warehouse_paths())
validate_offliner = validate.OneOf(Offliner.all())
validate_status = validate.OneOf(TaskStatus.all())
validate_event = validate.OneOf(TaskStatus.all_events())
validate_worker_name = validate.Length(min=3)
validate_periodicity = validate.OneOf(SchedulePeriodicity.all())


def validate_multiple_of_100(value):
    return value % 100 == 0


# reusable fields
skip_field = fields.Integer(required=False, missing=0, validate=validate.Range(min=0))
limit_field_20_500 = fields.Integer(
    required=False, missing=20, validate=validate.Range(min=0, max=500)
)
limit_field_20_200 = fields.Integer(
    required=False, missing=20, validate=validate.Range(min=0, max=200)
)
priority_field = fields.Integer(required=False, validate=validate_priority)
worker_field = fields.String(required=False, validate=validate_worker_name)
schedule_name_field = fields.String(validate=validate_schedule_name)
category_field = fields.String(required=False, validate=validate_category)
periodicity_field = fields.String(required=False, validate=validate_periodicity)
tag_field = fields.List(fields.String(validate=validate_not_empty), required=False)
offliner_field = fields.String(required=False, validate=validate_offliner)
email_field = fields.Email(required=False, validate=validate_not_empty)
username_field = fields.String(required=True, validate=validate_not_empty)
