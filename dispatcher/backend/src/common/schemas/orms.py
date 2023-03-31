import json

import marshmallow.fields as mf
from marshmallow import post_dump
from marshmallow_sqlalchemy import SQLAlchemySchema, auto_field

import db.models as dbm
from common.roles import get_role_for


class BaseSchema(SQLAlchemySchema):
    SKIP_VALUES = set([None])

    @post_dump
    def remove_skip_values(self, data, **kwargs):
        if isinstance(data, (list, tuple, set)):
            return type(data)(self.remove_skip_values(x) for x in data if x)
        elif isinstance(data, dict):
            return type(data)(
                (k, self.remove_skip_values(v))
                for k, v in data.items()
                if self.remove_skip_values(v)
            )
        else:
            return data


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
