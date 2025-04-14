from marshmallow import ValidationError, fields, validate

from common.enum import (
    Offliner,
    Platform,
    ScheduleCategory,
    SchedulePeriodicity,
    TaskStatus,
    WarehousePath,
)
from common.roles import ROLES
from common.schemas import String

# validators
validate_priority = validate.Range(min=0, max=10)


def validate_schedule_name(value) -> bool:
    if value == "none":
        raise ValidationError("`none` is a restricted keyword")
    if not value.strip() or value != value.strip():
        raise ValidationError(
            "Recipe name cannot contain leading and/or trailing space(s)"
        )
    return True


validate_not_empty = validate.Length(min=1)
validate_role = validate.OneOf(ROLES.keys())
validate_cpu = validate.Range(min=0)
validate_memory = validate.Range(min=0)
validate_disk = validate.Range(min=0)
validate_lang_code = validate.Length(min=2, max=3)
validate_output = validate.Equal("/output")
validate_category = validate.OneOf(ScheduleCategory.all())
validate_warehouse_path = validate.OneOf(WarehousePath.all())
validate_offliner = validate.OneOf(Offliner.all())
validate_status = validate.OneOf(TaskStatus.all())
validate_event = validate.OneOf(TaskStatus.all_events())
validate_worker_name = validate.Length(min=3)
validate_periodicity = validate.OneOf(SchedulePeriodicity.all())
validate_platform = validate.OneOf(Platform.all())
validate_platform_value = validate.Range(min=0)
# slack target must start with # for channels or @ for usernames
validate_slack_target = validate.Regexp(regex=r"^[#|@].+$")
validate_zim_filename = validate.Regexp(
    regex=r"^(.+?_)([a-z\-]{2,3}?_)(.+_|)([\d]{4}-[\d]{2}|{period}).zim$",
    error="ZIM filename format is incorrect",
)
validate_zim_title = validate.Length(max=30)
validate_zim_description = validate.Length(max=80)
validate_zim_longdescription = validate.Length(max=4000)


def validate_multiple_of_100(value):
    return value % 100 == 0


# reusable fields
skip_field = fields.Integer(
    required=False, load_default=0, validate=validate.Range(min=0)
)
limit_field_20_500 = fields.Integer(
    required=False, load_default=20, validate=validate.Range(min=0, max=500)
)
limit_field_20_200 = fields.Integer(
    required=False, load_default=20, validate=validate.Range(min=0, max=200)
)
priority_field = fields.Integer(required=False, validate=validate_priority)
worker_field = String(required=False, validate=validate_worker_name)
schedule_name_field = String(validate=validate_schedule_name)
category_field = String(required=False, validate=validate_category)
periodicity_field = String(required=False, validate=validate_periodicity)
tag_field = fields.List(String(validate=validate_not_empty), required=False)
offliner_field = String(required=False, validate=validate_offliner)
email_field = fields.Email(required=False, validate=validate_not_empty)
username_field = String(required=True, validate=validate_not_empty)


def validate_sort_order(value):
    """Validate that sort order is either 'asc' or 'desc'"""
    if value not in ["asc", "desc"]:
        raise ValidationError("Sort order must be either 'asc' or 'desc'")
    return True
