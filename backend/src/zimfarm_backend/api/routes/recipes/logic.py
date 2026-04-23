from http import HTTPStatus
from typing import Annotated, Any, cast
from uuid import UUID

import requests
from fastapi import APIRouter, Depends, Path, Query, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend import logger
from zimfarm_backend.api.routes.dependencies import (
    gen_dbsession,
    get_current_account,
    get_current_account_or_none,
    require_permission,
)
from zimfarm_backend.api.routes.http_errors import (
    BadRequestError,
    ForbiddenError,
    NotFoundError,
    ServerError,
    UnauthorizedError,
)
from zimfarm_backend.api.routes.models import ListResponse
from zimfarm_backend.api.routes.recipes.models import (
    CloneSchema,
    RecipeCreateResponseSchema,
    RecipeCreateSchema,
    RecipesGetSchema,
    RecipeUpdateSchema,
    RestoreRecipesSchema,
    RevertRecipeSchema,
    ToggleArchiveStatusSchema,
)
from zimfarm_backend.api.routes.utils import get_recipe_image_tags
from zimfarm_backend.common.enums import (
    DockerImageName,
    RecipeCategory,
    RecipePeriodicity,
)
from zimfarm_backend.common.schemas.fields import (
    LimitFieldMax200,
    NotEmptyString,
    SkipField,
)
from zimfarm_backend.common.schemas.models import (
    LanguageSchema,
    RecipeNotificationSchema,
    calculate_pagination_metadata,
)
from zimfarm_backend.common.schemas.orms import (
    OfflinerDefinitionSchema,
    RecipeConfigSchema,
    RecipeFullSchema,
    RecipeHistorySchema,
    RecipeLightSchema,
)
from zimfarm_backend.db.account import check_account_permission
from zimfarm_backend.db.exceptions import (
    RecordDoesNotExistError,
)
from zimfarm_backend.db.language import get_language_from_code
from zimfarm_backend.db.models import Account
from zimfarm_backend.db.offliner import get_offliner
from zimfarm_backend.db.offliner_definition import (
    create_offliner_definition_schema,
    create_offliner_instance,
    get_offliner_definition,
    get_offliner_definition_by_id,
)
from zimfarm_backend.db.recipe import create_recipe as db_create_recipe
from zimfarm_backend.db.recipe import (
    create_recipe_full_schema,
    create_recipe_history_schema,
    get_all_recipes,
)
from zimfarm_backend.db.recipe import delete_recipe as db_delete_recipe
from zimfarm_backend.db.recipe import get_recipe as db_get_recipe
from zimfarm_backend.db.recipe import get_recipe_history as db_get_recipe_history
from zimfarm_backend.db.recipe import (
    get_recipe_history_entry as db_get_recipe_history_entry,
)
from zimfarm_backend.db.recipe import get_recipes as db_get_recipes
from zimfarm_backend.db.recipe import (
    restore_recipes as db_restore_recipes,
)
from zimfarm_backend.db.recipe import revert_recipe as db_revert_recipe
from zimfarm_backend.db.recipe import (
    toggle_archive_status as db_toggle_archive_status,
)
from zimfarm_backend.db.recipe import update_recipe as db_update_recipe
from zimfarm_backend.utils.offliners import (
    expanded_config,
    get_image_name,
    get_image_prefix,
    get_key_differences,
)

router = APIRouter(prefix="/recipes", tags=["recipes"])
schedules_router = APIRouter(prefix="/schedules", tags=["schedules"])


@router.get("")
@schedules_router.get("")
def get_recipes(
    params: Annotated[RecipesGetSchema, Query()],
    current_account: Account | None = Depends(get_current_account_or_none),
    session: OrmSession = Depends(gen_dbsession),
) -> ListResponse[RecipeLightSchema]:
    if params.archived and not (
        current_account
        and check_account_permission(
            current_account, namespace="recipes", name="archive"
        )
    ):
        raise ForbiddenError("You are not allowed to view archived recipes.")

    results = db_get_recipes(
        session,
        skip=params.skip,
        limit=params.limit,
        lang=params.lang,
        categories=params.category,
        tags=params.tag,
        name=params.name,
        archived=params.archived,
        offliners=params.offliner,
    )
    return ListResponse(
        meta=calculate_pagination_metadata(
            nb_records=results.nb_records,
            skip=params.skip,
            limit=params.limit,
            page_size=len(results.recipes),
        ),
        items=cast(list[RecipeLightSchema], results.recipes),
    )


@router.post(
    "", dependencies=[Depends(require_permission(namespace="recipes", name="create"))]
)
@schedules_router.post(
    "", dependencies=[Depends(require_permission(namespace="recipes", name="create"))]
)
def create_recipe(
    request: RecipeCreateSchema,
    session: OrmSession = Depends(gen_dbsession),
    current_account: Account = Depends(get_current_account),
) -> JSONResponse:
    """Create a new recipe"""
    if offliner_id := request.config.get("offliner", {}).get("offliner_id"):
        offliner_definition = get_offliner_definition(
            session, offliner_id, request.version
        )
    else:
        raise RequestValidationError(
            [
                {
                    "loc": ["offliner"],
                    "msg": "Offliner information missing in config",
                    "type": "value_error",
                }
            ]
        )

    config = RecipeConfigSchema.model_validate(
        {
            **request.config,
            "offliner": create_offliner_instance(
                offliner=get_offliner(session, offliner_definition.offliner),
                offliner_definition=offliner_definition,
                data=request.config["offliner"],
                skip_validation=False,
                extra="ignore",
            ),
        }
    )

    # We need to compare the raw offliner config with the validated offliner
    # config to ensure the caller didn't pass extra fields for the offliner config
    raw_offliner_config = request.config.get("offliner", {})
    validated_offliner_dump = config.offliner.model_dump(mode="json")

    if extra_keys := get_key_differences(raw_offliner_config, validated_offliner_dump):
        raise RequestValidationError(
            [
                {
                    "loc": [key],
                    "msg": "Extra inputs are not permitted",
                    "type": "value_error",
                }
                for key in extra_keys
            ]
        )

    language = get_language_from_code(request.language)

    db_recipe = db_create_recipe(
        session,
        author_id=current_account.id,
        name=request.name,
        offliner_definition=offliner_definition,
        category=RecipeCategory(request.category),
        language=language,
        config=config,
        tags=request.tags,
        enabled=request.enabled,
        notification=request.notification,
        periodicity=request.periodicity,
        comment=request.comment,
        context=request.context.strip() if request.context else None,
    )

    return JSONResponse(
        content=RecipeCreateResponseSchema(
            id=db_recipe.id,
        ).model_dump(mode="json")
    )


@router.get("/backup")
@schedules_router.get("/backup")
def get_recipes_backup(
    session: OrmSession = Depends(gen_dbsession),
    current_account: Account | None = Depends(get_current_account_or_none),
    *,
    hide_secrets: Annotated[bool | None, Query()] = True,
    archived: Annotated[bool, Query()] = False,
) -> JSONResponse:
    """Get a list of recipes"""
    if not (
        current_account
        and check_account_permission(
            current_account, namespace="recipes", name="secrets"
        )
    ):
        exclude_notifications = True
    else:
        exclude_notifications = False

    # if the account doesn't have the appropriate permission, then their flag
    # does not matter
    if not (
        current_account
        and check_account_permission(
            current_account, namespace="recipes", name="secrets"
        )
    ):
        show_secrets = False
    else:
        show_secrets = not hide_secrets

    results = get_all_recipes(session, archived=archived)
    recipes = cast(list[RecipeFullSchema], results.recipes)
    content: list[dict[str, Any]] = []
    for recipe in recipes:
        if exclude_notifications:
            recipe.notification = None

        content.append(
            recipe.model_dump(mode="json", context={"show_secrets": show_secrets})
        )

    return JSONResponse(content=content)


@router.post(
    "/restore",
    dependencies=[Depends(require_permission(namespace="recipes", name="archive"))],
)
@schedules_router.post(
    "/restore",
    dependencies=[Depends(require_permission(namespace="recipes", name="archive"))],
)
def restore_archived_recipes(
    request: RestoreRecipesSchema,
    session: OrmSession = Depends(gen_dbsession),
    current_account: Account = Depends(get_current_account),
) -> Response:
    db_restore_recipes(
        session,
        recipe_names=request.recipe_names,
        actor_id=current_account.id,
        comment=request.comment,
    )
    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.get("/{recipe_name}")
@schedules_router.get("/{recipe_name}")
def get_recipe(
    recipe_name: Annotated[NotEmptyString, Path()],
    session: OrmSession = Depends(gen_dbsession),
    current_account: Account | None = Depends(get_current_account_or_none),
    *,
    hide_secrets: Annotated[bool | None, Query()] = True,
) -> JSONResponse:
    db_recipe = db_get_recipe(session, recipe_name=recipe_name)

    if current_account is None and db_recipe.archived:
        raise UnauthorizedError(
            "You do not have permissions to view an archived recipe."
        )

    offliner = get_offliner(session, db_recipe.config["offliner"]["offliner_id"])

    try:
        recipe = create_recipe_full_schema(db_recipe, offliner)
    except Exception as exc:
        logger.exception("error retrieving recipe")
        raise exc
    offliner_definition = get_offliner_definition_by_id(
        session, db_recipe.offliner_definition_id
    )

    if not (
        current_account
        and check_account_permission(
            current_account, namespace="recipes", name="secrets"
        )
    ):
        recipe.notification = None

    if not (
        current_account
        and check_account_permission(
            current_account, namespace="recipes", name="secrets"
        )
    ):
        show_secrets = False
    else:
        show_secrets = not hide_secrets

    # validity field in DB might not reflect the actual validity of the recipe
    # as constraints evolve
    try:
        create_recipe_full_schema(db_recipe, offliner, skip_validation=False)
    except ValidationError:
        recipe.is_valid = False

    recipe.config = expanded_config(
        cast(RecipeConfigSchema, recipe.config),
        offliner=offliner,
        offliner_definition=offliner_definition,
        show_secrets=show_secrets,
    )

    return JSONResponse(
        content=recipe.model_dump(mode="json", context={"show_secrets": show_secrets})
    )


@router.get("/{recipe_name}/similar")
@schedules_router.get("/{recipe_name}/similar")
def get_similar_recipe(
    recipe_name: Annotated[NotEmptyString, Path()],
    params: Annotated[RecipesGetSchema, Query()],
    session: OrmSession = Depends(gen_dbsession),
) -> ListResponse[RecipeLightSchema]:
    recipe = db_get_recipe(session, recipe_name=recipe_name)
    results = db_get_recipes(
        session,
        skip=params.skip,
        limit=params.limit,
        lang=params.lang,
        categories=params.category,
        tags=params.tag,
        archived=params.archived,
        similarity_data=recipe.similarity_data,
        omit_names=[recipe.name],
    )
    return ListResponse(
        meta=calculate_pagination_metadata(
            nb_records=results.nb_records,
            skip=params.skip,
            limit=params.limit,
            page_size=len(results.recipes),
        ),
        items=cast(list[RecipeLightSchema], results.recipes),
    )


@router.patch(
    "/{recipe_name}",
    dependencies=[Depends(require_permission(namespace="recipes", name="update"))],
)
@schedules_router.patch(
    "/{recipe_name}",
    dependencies=[Depends(require_permission(namespace="recipes", name="update"))],
)
def update_recipe(
    recipe_name: Annotated[NotEmptyString, Path()],
    request: RecipeUpdateSchema,
    session: OrmSession = Depends(gen_dbsession),
    current_account: Account = Depends(get_current_account),
) -> JSONResponse:
    db_recipe = db_get_recipe(session, recipe_name=recipe_name)
    if db_recipe.archived:
        raise BadRequestError("Cannot update an archived recipe")
    offliner = get_offliner(session, db_recipe.config["offliner"]["offliner_id"])
    recipe = create_recipe_full_schema(db_recipe, offliner)

    recipe_config = cast(RecipeConfigSchema, recipe.config)
    if not request.model_dump(exclude_unset=True):
        raise BadRequestError(
            "No changes were made to the recipe because no fields being set"
        )
    # track the definition to be used for updating the recipe
    offliner_definition: OfflinerDefinitionSchema

    if (
        request.offliner
        and request.offliner
        != recipe_config.offliner.offliner_id  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType]
    ):
        # Case 1: Attempting to change the offliner
        if not request.flags:
            raise BadRequestError("New flags must be set when changing offliner")

        if request.image is None:
            raise BadRequestError("New image must be set when changing offliner")

        if request.version is None:
            raise BadRequestError(
                "Flags definition version must be set when changing offliner"
            )
        offliner = get_offliner(session, request.offliner)

        offliner_definition = get_offliner_definition(
            session, request.offliner, request.version
        )

        # create a new recipe config for the new offliner validating the new flags
        new_recipe_config = RecipeConfigSchema.model_validate(
            {
                # reuse the existing config except for the offliner and image
                **recipe_config.model_dump(
                    mode="json",
                    exclude={"offliner", "image"},
                    context={"show_secrets": True},
                ),
                "image": {
                    "name": request.image.name,
                    "tag": request.image.tag,
                },
                "offliner": create_offliner_instance(
                    offliner=offliner,
                    offliner_definition=offliner_definition,
                    data={**request.flags, "offliner_id": request.offliner},
                    skip_validation=False,
                    extra="ignore",
                ),
            }
        )

        # determine if the caller passed extra fields for the new offliner config
        if extra_keys := get_key_differences(
            request.flags,
            new_recipe_config.offliner.model_dump(mode="json"),
        ):
            raise RequestValidationError(
                [
                    {
                        "loc": [key],
                        "msg": "Extra inputs are not permitted",
                        "type": "value_error",
                    }
                    for key in extra_keys
                ]
            )
    elif request.flags is not None:
        # Case 2: Attempting to change some flags but keep the offliner unchanged
        offliner = get_offliner(
            session,
            cast(
                str,
                recipe_config.offliner.offliner_id,  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType]
            ),
        )
        if request.version:
            # Create the new config based on new version
            offliner_definition = get_offliner_definition(
                session,
                offliner.id,
                request.version,
            )
        else:
            # Reuse the existing definition to validate
            offliner_definition = get_offliner_definition_by_id(
                session, recipe.offliner_definition_id
            )

        new_recipe_config = RecipeConfigSchema.model_validate(
            {
                **recipe_config.model_dump(
                    mode="json",
                    exclude={"offliner"},
                    context={"show_secrets": True},
                ),
                "offliner": create_offliner_instance(
                    offliner=offliner,
                    offliner_definition=offliner_definition,
                    data={**request.flags, "offliner_id": offliner_definition.offliner},
                    skip_validation=False,
                    extra="ignore",
                ),
            }
        )

        # determine if the caller passed extra fields for the offliner version
        if extra_keys := get_key_differences(
            request.flags,
            new_recipe_config.offliner.model_dump(mode="json"),
        ):
            raise RequestValidationError(
                [
                    {
                        "loc": [key],
                        "msg": "Extra inputs are not permitted",
                        "type": "value_error",
                    }
                    for key in extra_keys
                ]
            )
    else:
        # Case 3: Attempting to change a top level configuration that doesn't
        # affect the offliner
        new_recipe_config = recipe_config
        offliner_definition = get_offliner_definition_by_id(
            session, recipe.offliner_definition_id
        )

    if request.image is not None:
        # Ensure the image for the offliner is a valid preset
        new_offliner_name = cast(
            str,
            new_recipe_config.offliner.offliner_id,  # pyright: ignore[reportAttributeAccessIssue,reportUnknownMemberType]
        )
        try:
            DockerImageName[new_offliner_name]
        except KeyError as exc:
            raise BadRequestError(
                f"{new_offliner_name} does not have a docker image associated with it."
            ) from exc
        if get_image_prefix(new_offliner_name) + request.image.name != get_image_name(
            DockerImageName[new_offliner_name]
        ):
            raise BadRequestError("Image name must match selected offliner")

    # update the top-level recipe config attributes from the request but
    # exclude offliner as it means different things in request payload and config
    update_data = request.model_dump(
        exclude_unset=True,
        include={
            "warehouse_path",
            "image",
            "platform",
            "artifacts_globs",
            "monitor",
            "resources",
        },
    )
    new_recipe_config = new_recipe_config.model_copy(update=update_data)

    if request.language:
        try:
            language = get_language_from_code(request.language)
        except RecordDoesNotExistError as exc:
            raise BadRequestError(
                f"Language code {request.language} not found."
            ) from exc
    else:
        language = None

    recipe = db_update_recipe(
        session,
        recipe_name=recipe_name,
        author_id=current_account.id,
        comment=request.comment,
        new_recipe_config=new_recipe_config,
        language=language,
        name=request.name,
        category=request.category,
        tags=request.tags,
        enabled=request.enabled,
        periodicity=request.periodicity,
        # recipe must be valid if it has not failed validation yet
        is_valid=True,
        context=request.context,
        offliner_definition=offliner_definition,
        notification=request.notification,
    )

    recipe = create_recipe_full_schema(recipe, offliner)
    recipe.config = expanded_config(
        cast(RecipeConfigSchema, recipe.config),
        offliner=offliner,
        offliner_definition=offliner_definition,
        show_secrets=True,
    )
    return JSONResponse(
        content=recipe.model_dump(mode="json", context={"show_secrets": True})
    )


@router.delete(
    "/{recipe_name}",
    dependencies=[Depends(require_permission(namespace="recipes", name="delete"))],
)
@schedules_router.delete(
    "/{recipe_name}",
    dependencies=[Depends(require_permission(namespace="recipes", name="delete"))],
)
def delete_recipe(
    recipe_name: Annotated[NotEmptyString, Path()],
    session: OrmSession = Depends(gen_dbsession),
) -> Response:
    """Delete a recipe"""
    db_delete_recipe(session, recipe_name=recipe_name)
    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.get("/{recipe_name}/image-names")
@schedules_router.get("/{recipe_name}/image-names")
def get_recipe_image_names(
    recipe_name: Annotated[NotEmptyString, Path()],
    hub_name: Annotated[str, Query()],
    session: OrmSession = Depends(gen_dbsession),
) -> ListResponse[Any]:
    db_get_recipe(session, recipe_name=recipe_name)
    try:
        tags = get_recipe_image_tags(hub_name)
    except requests.HTTPError as exc:
        if exc.response.status_code == HTTPStatus.NOT_FOUND:
            raise NotFoundError("Image tags not found for recipe") from exc
        raise ServerError(
            "An unexpected error occurred while fetching image tags: "
            f"{exc.response.reason}"
        ) from exc
    except requests.RequestException as exc:
        raise ServerError(
            "An unexpected error occurred while fetching image tags: "
        ) from exc

    return ListResponse(
        items=tags,
        meta=calculate_pagination_metadata(
            nb_records=len(tags), skip=0, limit=len(tags), page_size=len(tags)
        ),
    )


@router.post(
    "/{recipe_name}/clone",
    dependencies=[Depends(require_permission(namespace="recipes", name="create"))],
)
@schedules_router.post(
    "/{recipe_name}/clone",
    dependencies=[Depends(require_permission(namespace="recipes", name="create"))],
)
def clone_recipe(
    recipe_name: Annotated[NotEmptyString, Path()],
    request: CloneSchema,
    session: OrmSession = Depends(gen_dbsession),
    current_account: Account = Depends(get_current_account),
) -> RecipeCreateResponseSchema:
    recipe = db_get_recipe(session, recipe_name=recipe_name)
    if recipe.archived:
        raise BadRequestError("You cannot clone an archived recipe.")

    # Skip validation while cloning a recipe
    try:
        language = get_language_from_code(recipe.language_code)
    except RecordDoesNotExistError:
        language = LanguageSchema.model_validate(
            {"code": recipe.language_code, "name": recipe.language_code},
            context={"skip_validation": True},
        )
    offliner = get_offliner(session, recipe.config["offliner"]["offliner_id"])

    new_recipe = db_create_recipe(
        session,
        author_id=current_account.id,
        comment=request.comment,
        name=request.name,
        category=RecipeCategory(recipe.category),
        config=RecipeConfigSchema.model_validate(
            {
                **recipe.config,
                "offliner": create_offliner_instance(
                    offliner=offliner,
                    offliner_definition=create_offliner_definition_schema(
                        recipe.offliner_definition
                    ),
                    data=recipe.config["offliner"],
                    skip_validation=True,
                ),
            },
            context={"skip_validation": True},
        ),
        tags=recipe.tags,
        enabled=False,
        notification=(
            RecipeNotificationSchema.model_validate(recipe.notification)
            if recipe.notification
            else None
        ),
        periodicity=RecipePeriodicity(recipe.periodicity),
        language=language,
        context=recipe.context,
        offliner_definition=create_offliner_definition_schema(
            recipe.offliner_definition
        ),
    )

    # validate the new recipe as we skipped validation to allow accounts clone
    # an invalid recipe. If validation fails, mark as invalid
    try:
        create_recipe_full_schema(new_recipe, offliner, skip_validation=False)
    except ValidationError:
        db_update_recipe(
            session,
            recipe_name=new_recipe.name,
            author_id=current_account.id,
            is_valid=False,
            offliner_definition=create_offliner_definition_schema(
                new_recipe.offliner_definition
            ),
        )

    return RecipeCreateResponseSchema(
        id=new_recipe.id,
    )


@router.patch(
    "/{recipe_name}/archive",
    dependencies=[Depends(require_permission(namespace="recipes", name="archive"))],
)
@schedules_router.patch(
    "/{recipe_name}/archive",
    dependencies=[Depends(require_permission(namespace="recipes", name="archive"))],
)
def archive_recipe(
    recipe_name: Annotated[NotEmptyString, Path()],
    request: ToggleArchiveStatusSchema,
    session: OrmSession = Depends(gen_dbsession),
    current_account: Account = Depends(get_current_account),
) -> JSONResponse:
    """Archive a recipe"""
    db_toggle_archive_status(
        session,
        recipe_name=recipe_name,
        archived=True,
        actor_id=current_account.id,
        comment=request.comment,
    )
    return JSONResponse(
        content={"message": f"Recipe '{recipe_name}' has been archived"},
        status_code=HTTPStatus.OK,
    )


@router.patch(
    "/{recipe_name}/restore",
    dependencies=[Depends(require_permission(namespace="recipes", name="archive"))],
)
@schedules_router.patch(
    "/{recipe_name}/restore",
    dependencies=[Depends(require_permission(namespace="recipes", name="archive"))],
)
def restore_archived_recipe(
    recipe_name: Annotated[NotEmptyString, Path()],
    request: ToggleArchiveStatusSchema,
    session: OrmSession = Depends(gen_dbsession),
    current_account: Account = Depends(get_current_account),
) -> JSONResponse:
    """Restore an archived recipe"""
    db_toggle_archive_status(
        session,
        recipe_name=recipe_name,
        archived=False,
        actor_id=current_account.id,
        comment=request.comment,
    )
    return JSONResponse(
        content={"message": f"Recipe '{recipe_name}' has been restored"},
        status_code=HTTPStatus.OK,
    )


@router.get(
    "/{recipe_name}/validate",
    dependencies=[Depends(require_permission(namespace="recipes", name="update"))],
)
@schedules_router.get(
    "/{recipe_name}/validate",
    dependencies=[Depends(require_permission(namespace="recipes", name="update"))],
)
def validate_recipe(
    recipe_name: Annotated[NotEmptyString, Path()],
    session: Annotated[OrmSession, Depends(gen_dbsession)],
) -> JSONResponse:
    recipe = db_get_recipe(session, recipe_name=recipe_name)
    offliner = get_offliner(session, recipe.config["offliner"]["offliner_id"])

    try:
        create_recipe_full_schema(recipe, offliner, skip_validation=False)
    except ValidationError as exc:
        raise RequestValidationError(exc.errors()) from exc

    return JSONResponse(content={"message": "Recipe validated with success"})


@router.get(
    "/{recipe_name}/history",
    dependencies=[Depends(require_permission(namespace="recipes", name="secrets"))],
)
@schedules_router.get(
    "/{recipe_name}/history",
    dependencies=[Depends(require_permission(namespace="recipes", name="secrets"))],
)
def get_recipe_history(
    recipe_name: Annotated[NotEmptyString, Path()],
    session: OrmSession = Depends(gen_dbsession),
    skip: Annotated[SkipField, Query()] = 0,
    limit: Annotated[LimitFieldMax200, Query()] = 200,
) -> ListResponse[RecipeHistorySchema]:
    recipe = db_get_recipe(session, recipe_name=recipe_name)

    results = db_get_recipe_history(
        session, recipe_id=recipe.id, skip=skip, limit=limit
    )
    return ListResponse(
        items=results.history_entries,
        meta=calculate_pagination_metadata(
            nb_records=results.nb_records,
            skip=skip,
            limit=limit,
            page_size=len(results.history_entries),
        ),
    )


@router.get(
    "/{recipe_name}/history/{history_id}",
    dependencies=[Depends(require_permission(namespace="recipes", name="secrets"))],
)
@schedules_router.get(
    "/{recipe_name}/history/{history_id}",
    dependencies=[Depends(require_permission(namespace="recipes", name="secrets"))],
)
def get_recipe_history_entry(
    recipe_name: Annotated[NotEmptyString, Path()],
    history_id: Annotated[UUID, Path()],
    session: OrmSession = Depends(gen_dbsession),
) -> RecipeHistorySchema:
    history_entry = db_get_recipe_history_entry(
        session, recipe_name=recipe_name, history_id=history_id
    )
    return create_recipe_history_schema(history_entry)


@router.patch(
    "/{recipe_name}/revert/{history_id}",
    dependencies=[Depends(require_permission(namespace="recipes", name="update"))],
)
@schedules_router.patch(
    "/{recipe_name}/revert/{history_id}",
    dependencies=[Depends(require_permission(namespace="recipes", name="update"))],
)
def revert_recipe(
    recipe_name: Annotated[NotEmptyString, Path()],
    history_id: Annotated[UUID, Path()],
    request: RevertRecipeSchema,
    session: OrmSession = Depends(gen_dbsession),
    current_account: Account = Depends(get_current_account),
) -> JSONResponse:
    """Revert a recipe to a previous history."""
    db_revert_recipe(
        session,
        recipe_name=recipe_name,
        history_id=history_id,
        author_id=current_account.id,
        comment=request.comment,
    )
    return JSONResponse(
        content={"message": f"Recipe '{recipe_name}' has been restored"},
        status_code=HTTPStatus.OK,
    )
