from marshmallow import Schema, fields
from marshmallow.validate import And, ValidationError, Validator


class NoNullChar(Validator):
    """Validate that string value does not contains Unicode null character"""

    def __call__(self, value: str) -> str:
        if "\u0000" in value:
            raise ValidationError("Null character is not allowed")

        return value


class String(fields.String):
    """A custom String field for our needs

    In addition to base type checks, it also ensures that value does not contains
    Unicode null character
    """

    @property
    def _validate_all(self):
        return And(
            NoNullChar(),
            *self.validators,
            error=self.error_messages["validator_failed"]
        )


class ListOfStringEnum(fields.List):
    pass


class StringEnum(String):
    pass


class HexColor(String):
    pass


class LongString(String):
    pass


class SerializableSchema(Schema):
    MAPPING = {
        String: "text",
        fields.String: "text",
        LongString: "long-text",
        StringEnum: "string-enum",
        HexColor: "hex-color",
        fields.Url: "url",
        fields.Email: "email",
        fields.UUID: "text",
        fields.Boolean: "boolean",
        fields.Integer: "integer",
        fields.Float: "float",
        ListOfStringEnum: "list-of-string-enum",
        # fields.List: "list",
        # fields.Date: "date",
        # fields.Time: "text",
        # fields.DateTime: "text",
        # fields.TimeDelta: "text",
    }

    @classmethod
    def field_type_for(cls, field):
        return cls.MAPPING.get(field.__class__, "text")

    @classmethod
    def desc_field(cls, field):
        field_type = cls.field_type_for(field)
        desc = {
            "key": field.name,
            "type": field_type,
            "data_key": field.data_key or field.name,
            "required": field.required,
        }

        if field_type == "list-of-string-enum":
            desc["choices"] = field.inner.validate.choices

        if field_type == "string-enum":
            desc["choices"] = field.validate.choices

        if field.metadata:
            desc.update(field.metadata)

        return desc

    def to_desc(self):
        return list(map(self.desc_field, self.declared_fields.values()))

    @classmethod
    def ingest(cls, *args, **kwargs):
        return cls().dump(cls().load(*args, **kwargs))
