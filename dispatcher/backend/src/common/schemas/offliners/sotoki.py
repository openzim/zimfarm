from marshmallow import fields, validate

from common.schemas import SerializableSchema
from common.schemas.fields import validate_output, validate_multiple_of_100


class SotokiFlagsSchema(SerializableSchema):
    class Meta:
        ordered = True

    domain = fields.String(
        metadata={
            "label": "Domain",
            "description": "Domain name of the stack exchange project.",
        },
        required=True,
    )

    publisher = fields.String(
        metadata={"label": "Publisher", "description": "ZIM Publisher metadata"},
        required=True,
    )

    directory = fields.String(
        metadata={
            "label": "Output folder",
            "placeholder": "/output",
            "description": "Output folder for ZIM file or build folder. Leave it as `/output`",
        },
        missing="/output",
        default="/output",
        validate=validate_output,
    )

    tag_depth = fields.Integer(
        required=False,
        data_key="tag-depth",
        metadata={
            "Label": "Tag Depth",
            "description": "Specify number of questions (ordered by Score), to show in tags pages. Otherwise (-1), all questions are shown. Must be a multiple of 100.",
        },
        validate=validate_multiple_of_100,
    )

    threads = fields.Integer(
        required=False,
        metadata={
            "label": "Threads",
            "description": "Number of threads to use, default is number_of_cores/2",
        },
        validate=validate.Range(min=1),
    )

    zimpath = fields.String(
        required=False,
        metadata={
            "label": "ZIM Path",
            "description": "Custom path name for the ZIM file. Make sure to prefix with `/work/`.",
        },
        validate=validate.Regexp(r"^/work/"),
    )

    nofulltextindex = fields.Boolean(
        required=False,
        metadata={"label": "No FullText Index", "description": "Don't Index content"},
    )

    ignoreoldsite = fields.Boolean(
        required=False,
        metadata={
            "label": "Allow Closed",
            "description": "Allow processing of closed domain using archive.org (if supported)",
        },
    )

    nopic = fields.Boolean(
        required=False,
        metadata={"label": "No Picture", "description": "Don't download pictures"},
    )

    no_userprofile = fields.Boolean(
        required=False,
        data_key="no-userprofile",
        metadata={
            "label": "No User Profile",
            "description": "Don't include user profiles",
        },
    )
