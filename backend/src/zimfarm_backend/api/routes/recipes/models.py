from typing import Any
from uuid import UUID

from pydantic import Field

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
    comment: str | None = None


class ToggleArchiveStatusSchema(BaseModel):
    comment: str | None = None


class RevertRecipeSchema(BaseModel):
    comment: str | None = None
