from typing import Literal, Self

from pydantic import ConfigDict, Field, model_validator

from zimfarm_backend.common.schemas import BaseModel, CamelModel
from zimfarm_backend.common.schemas.fields import NotEmptyString


class Choice(BaseModel):
    title: str
    value: str
    dependents: list[NotEmptyString] = Field(default_factory=list)


class BaseFlagSchema(BaseModel):
    title: str = Field(alias="label")
    description: str
    required: bool = False
    secret: bool = False
    min: int | None = None
    max: int | None = None
    min_graphemes: int | None = Field(validation_alias="minGraphemes", default=None)
    max_graphemes: int | None = Field(validation_alias="maxGraphemes", default=None)
    pattern: str | None = None
    allow_remote_url: bool = Field(default=False, validation_alias="allowRemoteUrl")


class PreparedBlob(BaseModel):
    """Blob data prepared for upload but not yet uploaded"""

    kind: str
    flag_name: str
    checksum: str
    data: bytes


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
        "color",
    ]
    kind: Literal["image", "css", "html", "txt", "illustration"] | None = None
    choices: list[str] | list[Choice] | None = None
    alias: str | None = None
    relaxed_pattern: str | None = Field(validation_alias="relaxedPattern", default=None)
    relaxed_min: int | None = Field(validation_alias="relaxedMin", default=None)
    relaxed_max: int | None = Field(validation_alias="relaxedMax", default=None)
    relaxed_min_graphemes: int | None = Field(
        validation_alias="relaxedMinGraphemes", default=None
    )
    relaxed_max_graphemes: int | None = Field(
        validation_alias="relaxedMaxGraphemes", default=None
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
    def check_blob_type(self) -> Self:
        """Validate that only blob types have a kind"""
        if self.type == "blob" and not self.kind:
            raise ValueError("Blob types must specify a kind")

        if self.type != "blob" and self.kind:
            raise ValueError("Only blob types should specify a kind")

        if self.allow_remote_url and self.type != "blob":
            raise ValueError("Only blob types should specify allow_remote_url")

        return self

    @model_validator(mode="after")
    def check_enum_types(self) -> Self:
        """Validate that only string-enum/list-of-string fields can have  choices.

        In addition, ensure that only string-enum types can have dependents set
        """
        enum_types = ("string-enum", "list-of-string-enum")
        if self.type not in enum_types and self.choices:
            raise ValueError(
                "Only string-enum and list-of-string-enum types should specify choices"
            )

        if self.type in enum_types and not self.choices:
            raise ValueError(
                "Choices are required for string-enum and list-of-string-enum types"
            )

        if self.type == "list-of-string-enum" and self.choices:
            dependent = next(
                (
                    dependent
                    for choice in self.choices
                    if not isinstance(choice, str)
                    for dependent in choice.dependents
                ),
                None,
            )
            if dependent:
                raise ValueError("Only string-enum types can set dependents.")

        return self

    @model_validator(mode="after")
    def validate_choice_dependents(self) -> Self:
        """Validate that the dependents for a choice field are mutually exclusive."""

        if self.choices:
            all_dependents = [
                dependent
                for choice in self.choices
                if not isinstance(choice, str)
                for dependent in choice.dependents
            ]
            if len(set(all_dependents)) != len(all_dependents):
                raise ValueError("Dependents must be unique and mutually exclusive")

        return self

    @model_validator(mode="after")
    def validate_unique_choices(self) -> Self:
        """Validate that the choice values and titles are unique"""

        if self.choices:
            titles: list[str] = []
            values: list[str] = []
            for choice in self.choices:
                if isinstance(choice, str):
                    titles.append(choice)
                    values.append(choice)
                else:
                    titles.append(choice.title)
                    values.append(choice.value)

            if len(set(titles)) != len(titles) or len(set(values)) != len(values):
                raise ValueError("Choice titles and values must be unique")

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


class ZimMetadata(CamelModel):
    metadata: str  # the name of the Metadata entry e.g Name, Language
    flag: str  # the flag that is used to generate this metadata


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
    zim_metadata: list[ZimMetadata] = Field(default_factory=list)  # pyright: ignore

    @model_validator(mode="after")
    def check_zim_metadata_fields(self) -> Self:
        """Ensure that for each metadata entry, it's flag exists in self.flags"""
        for entry in self.zim_metadata:
            if entry.flag not in self.flags:
                raise ValueError(f"{entry.flag} is not a in the flags dictionary")
        return self

    @model_validator(mode="after")
    def check_choice_fields(self) -> Self:
        """Ensure dependent values for choice fields are valid fields."""
        flag_names = set(self.flags.keys())
        for flag_name, flag in self.flags.items():
            if not flag.choices:
                continue

            for choice in flag.choices:
                if isinstance(choice, str):
                    continue

                dependents = set(choice.dependents)
                if flag_name in dependents:
                    raise ValueError(f"Flag '{flag_name}' cannot depend on itself")

                differences = dependents - flag_names
                if differences:
                    raise ValueError(
                        f"Dependents ({','.join(differences)}) for choice field "
                        f"'{flag_name}' are not valid flag names"
                    )

        return self
