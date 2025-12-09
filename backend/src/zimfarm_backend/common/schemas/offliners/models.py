from typing import Literal, Self

from pydantic import ConfigDict, Field, model_validator

from zimfarm_backend.common.schemas import BaseModel, CamelModel


class Choice(BaseModel):
    title: str
    value: str


class BaseFlagSchema(BaseModel):
    title: str = Field(alias="label")
    description: str
    required: bool = False
    secret: bool = False
    min: int | None = None
    max: int | None = None
    min_length: int | None = Field(validation_alias="minLength", default=None)
    max_length: int | None = Field(validation_alias="maxLength", default=None)
    pattern: str | None = None


class FlagSchema(BaseFlagSchema):
    type: Literal[
        "string",
        "boolean",
        "float",
        "integer",
        "url",
        "email",
        "string-enum",
        "list-of-integer",
        "list-of-string",
        "list-of-boolean",
        "list-of-string-enum",
        "list-of-url",
        "list-of-email",
        "blob",
    ]
    kind: Literal["image", "css"] | None = None
    choices: list[str] | list[Choice] | None = None
    alias: str | None = None
    relaxed_pattern: str | None = Field(validation_alias="relaxedPattern", default=None)
    relaxed_min: int | None = Field(validation_alias="relaxedMin", default=None)
    relaxed_max: int | None = Field(validation_alias="relaxedMax", default=None)
    relaxed_min_length: int | None = Field(
        validation_alias="relaxedMinLength", default=None
    )
    relaxed_max_length: int | None = Field(
        validation_alias="relaxedMaxLength", default=None
    )
    custom_validator: str | None = Field(
        validation_alias="customValidator", default=None
    )
    default: str | bool | None = None
    frozen: bool | None = None
    is_publisher: bool = Field(default=False, validation_alias="isPublisher")

    @model_validator(mode="after")
    def check_frozen_fields(self) -> Self:
        """Validate that a frozen field has a default"""
        if self.frozen and not self.default:
            raise ValueError("Frozen fields should have a default")

        return self

    @model_validator(mode="after")
    def check_type(self) -> Self:
        """Validate that only blob types have a kind"""
        if self.type == "blob" and not self.kind:
            raise ValueError("Blob types must specify a kind")

        if self.type != "blob" and self.kind:
            raise ValueError("Only blob types should specify a kind")

        return self

    # disallow extra fields so that we fail early validation time. Helps with cases
    # where we mistype a value in the schema rather than the field being omitted which
    # is a harder issue to track
    model_config = ConfigDict(extra="forbid")


class ModelValidatorSchema(CamelModel):
    """Schema for defining the validators that should apply at the model level"""

    name: str  # name of the validator function
    fields: list[str]  # list of field names to call the function with
    model_config = ConfigDict(extra="forbid")


class TransformerSchema(CamelModel):
    # the name of the transformer function to use for the field. If None, the field
    # will be used as it is
    name: Literal["split", "hostname"] | None = None
    # the operand to use for the transformer function (if the function
    # takes an operand)
    operand: str | None = None


class SimilarityDataSchema(CamelModel):
    # the name of the flag to use for the similarity data
    flag: str
    # transformers are applied in sequential order
    transformers: list[TransformerSchema]


class OfflinerSpecSchema(CamelModel):
    flags: dict[str, FlagSchema]
    model_validators: list[ModelValidatorSchema] = Field(  # pyright: ignore
        default_factory=list,
    )
    std_output: str | bool = Field(default=False)
    std_stats: str | bool = Field(default=False)
    similarity_data: list[SimilarityDataSchema] = Field(  # pyright: ignore
        default_factory=list
    )
