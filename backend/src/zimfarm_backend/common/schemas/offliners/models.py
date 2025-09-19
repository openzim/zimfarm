from pydantic import Field

from zimfarm_backend.common.schemas import BaseModel


class Choice(BaseModel):
    title: str
    value: str


class BaseFlagSchema(BaseModel):
    title: str = Field(serialization_alias="label")
    description: str
    required: bool = False
    secret: bool = False
    min: int | None = None
    max: int | None = None
    min_length: int | None = Field(validation_alias="minLength", default=None)
    max_length: int | None = Field(validation_alias="maxLength", default=None)
    pattern: str | None = None
