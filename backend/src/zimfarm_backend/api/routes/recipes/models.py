from typing import Any, Self
from uuid import UUID

from pydantic import Field
from pydantic.functional_validators import model_validator

from zimfarm_backend.common.enums import (
    RecipeCategory,
    RecipePeriodicity,
)
from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.common.schemas.fields import (
    LimitFieldMax200,
    NotEmptyString,
    PlatformField,
    RecipeNameField,
    SkipField,
    WarehousePathField,
    ZIMLangCode,
)
from zimfarm_backend.common.schemas.models import (
    DockerImageSchema,
    RecipeNotificationSchema,
    ResourcesSchema,
)


class RecipesGetSchema(BaseModel):
    skip: SkipField = 0
    limit: LimitFieldMax200 = 20
    category: list[RecipeCategory] | None = None
    tag: list[NotEmptyString] | None = None
    lang: list[NotEmptyString] | None = None
    name: NotEmptyString | None = None
    archived: bool = False
    offliner: list[NotEmptyString] | None = None


class RecipeCreateSchema(BaseModel):
    name: RecipeNameField
    language: ZIMLangCode
    category: RecipeCategory
    periodicity: RecipePeriodicity
    tags: list[NotEmptyString] = Field(default_factory=list)
    enabled: bool
    version: NotEmptyString
    config: dict[str, Any]  # will be validated in the route
    notification: RecipeNotificationSchema | None = None
    context: str | None = None
    comment: str | None = None


class RecipeCreateResponseSchema(BaseModel):
    id: UUID


class RecipeUpdateSchema(BaseModel):
    name: RecipeNameField | None = None
    language: ZIMLangCode | None = None
    category: RecipeCategory | None = None
    periodicity: RecipePeriodicity | None = None
    tags: list[NotEmptyString] | None = None
    enabled: bool | None = None
    offliner: str | None = None
    warehouse_path: WarehousePathField | None = None
    image: DockerImageSchema | None = None
    platform: PlatformField | None = None
    resources: ResourcesSchema | None = None
    monitor: bool | None = None
    flags: dict[str, Any] | None = None
    artifacts_globs: list[NotEmptyString] | None = None
    context: str | None = None
    version: str | None = None
    comment: str | None = None  # Optional comment for history tracking
    notification: RecipeNotificationSchema | None = None


class CloneSchema(BaseModel):
    name: RecipeNameField
    comment: str | None = None


class RestoreRecipesSchema(BaseModel):
    recipe_names: list[RecipeNameField] = Field(default_factory=list)
    schedule_names: list[RecipeNameField] = Field(
        default_factory=list
    )  # Kept for compatibility purposes
    comment: str | None = None

    @model_validator(mode="after")
    def check_recipe_names(self) -> Self:
        if self.recipe_names and self.schedule_names:
            raise ValueError("Only one of schedule_names and recipe_names must be set")
        if not (self.recipe_names or self.schedule_names):
            raise ValueError("One of schedule_names and recipe_names must be set")

        if self.schedule_names:
            self.recipe_names = self.schedule_names

        return self


class ToggleArchiveStatusSchema(BaseModel):
    comment: str | None = None


class RevertRecipeSchema(BaseModel):
    comment: str | None = None
