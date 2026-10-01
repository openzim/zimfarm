from collections.abc import Sequence
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
    get_editable_team_ids,
    get_viewable_team_ids,
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
    RecipeHistorySchema,
    RecipeLightSchema,
)
from zimfarm_backend.db import account as db_account
from zimfarm_backend.db import language as db_language
from zimfarm_backend.db import models as db_models
from zimfarm_backend.db import offliner as db_offliner
from zimfarm_backend.db import offliner_definition as db_offliner_definition
from zimfarm_backend.db import recipe as db_recipe
from zimfarm_backend.db import team as db_team
from zimfarm_backend.db.exceptions import RecordDoesNotExistError
from zimfarm_backend.utils.offliners import (
    clear_unset_choices_dependents,
    expanded_config,
    get_image_name,
    get_image_prefix,
    get_key_differences,
)

router = APIRouter(prefix="/recipes", tags=["recipes"])


@router.get("")
def get_recipes(
    params: Annotated[RecipesGetSchema, Query()],
    current_account: db_models.Account | None = Depends(get_current_account_or_none),
    session: OrmSession = Depends(gen_dbsession),
    accessible_team_ids: Sequence[UUID] | None = Depends(get_viewable_team_ids),
) -> ListResponse[RecipeLightSchema]:
    if params.archived and not (
        current_account
        and db_account.check_account_permission(
            current_account, namespace="recipes", name="archive"
        )
    ):
        raise ForbiddenError("You are not allowed to view archived recipes.")

    results = db_recipe.get_recipes(
        session,
        skip=params.skip,
        limit=params.limit,
        accessible_team_ids=accessible_team_ids,
        lang=params.lang,
        tags=params.tag,
        name=params.name,
        archived=params.archived,
        offliners=params.offliner,
        teams=params.team,
    )
    return ListResponse(
        meta=calculate_pagination_metadata(
            nb_records=results.nb_records,
            skip=params.skip,
            limit=params.limit,
            page_size=len(results.records),
        ),
        items=results.records,
    )


@router.post(
    "", dependencies=[Depends(require_permission(namespace="recipes", name="create"))]
)
def create_recipe(
    request: RecipeCreateSchema,
    session: OrmSession = Depends(gen_dbsession),
    current_account: db_models.Account = Depends(get_current_account),
    accessible_team_ids: Sequence[UUID] | None = Depends(get_editable_team_ids),
) -> JSONResponse:
    """Create a new recipe"""
    if offliner_id := request.config.get("offliner", {}).get("offliner_id"):
        offliner_definition = db_offliner_definition.get_offliner_definition(
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

    offliner = db_offliner.get_offliner(session, offliner_definition.offliner)

    data = clear_unset_choices_dependents(
        offliner_definition.schema_, request.config["offliner"], offliner.base_model
    )

    config = RecipeConfigSchema.model_validate(
        {
            **request.config,
            "offliner": db_offliner_definition.create_offliner_instance(
                offliner=offliner,
                offliner_definition=offliner_definition,
                data=data,
                skip_validation=False,
                extra="ignore",
            ),
        }
    )

    # We need to compare the raw offliner config with the validated offliner
    # config to ensure the caller didn't pass extra fields for the offliner config
    raw_offliner_config = data
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

    language = db_language.get_language_from_code(request.language)

    payload = db_recipe.RecipeCreateSchema(
        name=request.name,
        language=language,
        config=config,
        tags=list(request.tags),
        enabled=request.enabled,
        notification=request.notification,
        periodicity=request.periodicity,
        context=request.context.strip() if request.context else None,
        comment=request.comment,
        teams=request.teams,
    )

    recipe_model = db_recipe.create_recipe(
        session,
        author_id=current_account.id,
        payload=payload,
        offliner_definition=offliner_definition,
        accessible_team_ids=accessible_team_ids,
    )

    return JSONResponse(
        content=RecipeCreateResponseSchema(
            id=recipe_model.id,
        ).model_dump(mode="json")
    )


@router.get("/backup")
def get_recipes_backup(
    session: OrmSession = Depends(gen_dbsession),
    current_account: db_models.Account | None = Depends(get_current_account_or_none),
    accessible_team_ids: Sequence[UUID] | None = Depends(get_viewable_team_ids),
    *,
    hide_secrets: Annotated[bool | None, Query()] = True,
    archived: Annotated[bool, Query()] = False,
) -> JSONResponse:
    """Get a list of recipes"""
    if not (
        current_account
        and db_account.check_account_permission(
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
        and db_account.check_account_permission(
            current_account, namespace="recipes", name="secrets"
        )
    ):
        show_secrets = False
    else:
        show_secrets = not hide_secrets

    results = db_recipe.get_all_recipes(
        session, archived=archived, accessible_team_ids=accessible_team_ids
    )
    recipes = results.records
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
def restore_archived_recipes(
    request: RestoreRecipesSchema,
    session: OrmSession = Depends(gen_dbsession),
    current_account: db_models.Account = Depends(get_current_account),
    accessible_team_ids: Sequence[UUID] | None = Depends(get_editable_team_ids),
) -> Response:
    db_recipe.restore_recipes(
        session,
        recipe_identifiers=request.recipe_names
        or [str(recipe_id) for recipe_id in request.recipe_ids],
        actor_id=current_account.id,
        accessible_team_ids=accessible_team_ids,
        comment=request.comment,
    )
    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.get("/{recipe_identifier}")
def get_recipe(
    recipe_identifier: Annotated[NotEmptyString, Path()],
    session: OrmSession = Depends(gen_dbsession),
    current_account: db_models.Account | None = Depends(get_current_account_or_none),
    accessible_team_ids: Sequence[UUID] | None = Depends(get_viewable_team_ids),
    *,
    hide_secrets: Annotated[bool | None, Query()] = True,
) -> JSONResponse:
    recipe_model = db_recipe.get_recipe(
        session, recipe_identifier, accessible_team_ids=accessible_team_ids
    )

    if current_account is None and recipe_model.archived:
        raise UnauthorizedError(
            "You do not have permissions to view an archived recipe."
        )

    offliner = db_offliner.get_offliner(
        session, recipe_model.config["offliner"]["offliner_id"]
    )

    try:
        recipe = db_recipe.create_recipe_full_schema(recipe_model, offliner)
    except Exception as exc:
        logger.exception("error retrieving recipe")
        raise exc
    offliner_definition = db_offliner_definition.get_offliner_definition_by_id(
        session, recipe_model.offliner_definition_id
    )

    if not (
        current_account
        and db_account.check_account_permission(
            current_account, namespace="recipes", name="secrets"
        )
    ):
        recipe.notification = None

    if not (
        current_account
        and db_account.check_account_permission(
            current_account, namespace="recipes", name="secrets"
        )
    ):
        show_secrets = False
    else:
        show_secrets = not hide_secrets

    # validity field in DB might not reflect the actual validity of the recipe
    # as constraints evolve
    try:
        db_recipe.create_recipe_full_schema(
            recipe_model, offliner, skip_validation=False
        )
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


@router.get("/{recipe_identifier}/similar")
def get_similar_recipe(
    recipe_identifier: Annotated[NotEmptyString, Path()],
    params: Annotated[RecipesGetSchema, Query()],
    session: OrmSession = Depends(gen_dbsession),
    accessible_team_ids: Sequence[UUID] | None = Depends(get_viewable_team_ids),
) -> ListResponse[RecipeLightSchema]:
    recipe = db_recipe.get_recipe(
        session, recipe_identifier, accessible_team_ids=accessible_team_ids
    )
    results = db_recipe.get_recipes(
        session,
        skip=params.skip,
        limit=params.limit,
        accessible_team_ids=accessible_team_ids,
        lang=params.lang,
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
            page_size=len(results.records),
        ),
        items=results.records,
    )


@router.patch(
    "/{recipe_identifier}",
    dependencies=[Depends(require_permission(namespace="recipes", name="update"))],
)
def update_recipe(
    recipe_identifier: Annotated[NotEmptyString, Path()],
    request: RecipeUpdateSchema,
    session: OrmSession = Depends(gen_dbsession),
    current_account: db_models.Account = Depends(get_current_account),
    accessible_team_ids: Sequence[UUID] | None = Depends(get_editable_team_ids),
) -> JSONResponse:
    recipe_model = db_recipe.get_recipe(
        session, recipe_identifier, accessible_team_ids=accessible_team_ids
    )
    if recipe_model.archived:
        raise BadRequestError("Cannot update an archived recipe")
    offliner = db_offliner.get_offliner(
        session, recipe_model.config["offliner"]["offliner_id"]
    )
    recipe = db_recipe.create_recipe_full_schema(recipe_model, offliner)

    recipe_config = cast(RecipeConfigSchema, recipe.config)
    if not request.model_dump(exclude_unset=True):
        raise BadRequestError(
            "No changes were made to the recipe because no fields being set"
        )
    # track the definition to be used for updating the recipe
    offliner_definition: OfflinerDefinitionSchema

    if (
        request.offliner and request.offliner != recipe_config.offliner.offliner_id  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType]
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
        offliner = db_offliner.get_offliner(session, request.offliner)

        offliner_definition = db_offliner_definition.get_offliner_definition(
            session, request.offliner, request.version
        )

        # create a new recipe config for the new offliner validating the new flags
        flags = clear_unset_choices_dependents(
            offliner_definition.schema_, request.flags, offliner.base_model
        )
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
                "offliner": db_offliner_definition.create_offliner_instance(
                    offliner=offliner,
                    offliner_definition=offliner_definition,
                    data={**flags, "offliner_id": request.offliner},
                    skip_validation=False,
                    extra="ignore",
                ),
            }
        )

        # determine if the caller passed extra fields for the new offliner config
        if extra_keys := get_key_differences(
            flags,
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
        offliner = db_offliner.get_offliner(
            session,
            cast(
                str,
                recipe_config.offliner.offliner_id,  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType]
            ),
        )
        if request.version:
            # Create the new config based on new version
            offliner_definition = db_offliner_definition.get_offliner_definition(
                session,
                offliner.id,
                request.version,
            )
        else:
            # Reuse the existing definition to validate
            offliner_definition = db_offliner_definition.get_offliner_definition_by_id(
                session, recipe.offliner_definition_id
            )

        flags = clear_unset_choices_dependents(
            offliner_definition.schema_, request.flags, offliner.base_model
        )
        new_recipe_config = RecipeConfigSchema.model_validate(
            {
                **recipe_config.model_dump(
                    mode="json",
                    exclude={"offliner"},
                    context={"show_secrets": True},
                ),
                "offliner": db_offliner_definition.create_offliner_instance(
                    offliner=offliner,
                    offliner_definition=offliner_definition,
                    data={**flags, "offliner_id": offliner_definition.offliner},
                    skip_validation=False,
                    extra="ignore",
                ),
            }
        )

        # determine if the caller passed extra fields for the offliner version
        if extra_keys := get_key_differences(
            flags,
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
        offliner_definition = db_offliner_definition.get_offliner_definition_by_id(
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
            language = db_language.get_language_from_code(request.language)
        except RecordDoesNotExistError as exc:
            raise BadRequestError(
                f"Language code {request.language} not found."
            ) from exc
    else:
        language = None

    update_payload = db_recipe.RecipeUpdateSchema(
        offliner_definition=offliner_definition,
        config=new_recipe_config,
        language=language,
        name=request.name,
        tags=request.tags,
        teams=request.teams,
        enabled=request.enabled,
        periodicity=request.periodicity,
        # recipe must be valid if it has not failed validation yet
        is_valid=True,
        context=request.context,
        comment=request.comment,
        notification=request.notification,
    )

    recipe = db_recipe.update_recipe(
        session,
        recipe_identifier=recipe_identifier,
        author_id=current_account.id,
        accessible_team_ids=accessible_team_ids,
        payload=update_payload,
    )

    recipe = db_recipe.create_recipe_full_schema(recipe, offliner)
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
    "/{recipe_identifier}",
    dependencies=[Depends(require_permission(namespace="recipes", name="delete"))],
)
def delete_recipe(
    recipe_identifier: Annotated[NotEmptyString, Path()],
    session: OrmSession = Depends(gen_dbsession),
    accessible_team_ids: Sequence[UUID] | None = Depends(get_editable_team_ids),
) -> Response:
    """Delete a recipe"""
    db_recipe.delete_recipe(session, recipe_identifier, accessible_team_ids)
    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.get("/{recipe_identifier}/image-names")
def get_recipe_image_names(
    recipe_identifier: Annotated[NotEmptyString, Path()],
    hub_name: Annotated[str, Query()],
    session: OrmSession = Depends(gen_dbsession),
    accessible_team_ids: Sequence[UUID] | None = Depends(get_viewable_team_ids),
) -> ListResponse[Any]:
    db_recipe.get_recipe(
        session, recipe_identifier, accessible_team_ids=accessible_team_ids
    )
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


def _resolve_clone_teams(
    session: OrmSession,
    *,
    request_teams: list[str] | None,
    source_team_names: list[str],
    editable_team_ids: Sequence[UUID] | None,
) -> list[str]:
    """Determine which teams should own a cloned recipe.

    - Global accounts may assign any team and default to the source recipe's teams.
    - Team-scoped accounts may only assign teams they belong to.
    """
    # global roles can assign any team
    if editable_team_ids is None:
        return request_teams if request_teams else source_team_names

    editable_team_names = db_team.get_team_names(session, editable_team_ids)

    if request_teams:
        if unowned_teams := set(request_teams) - set(editable_team_names):
            raise ForbiddenError(
                "You are not allowed to create a recipe for team(s): "
                + ", ".join(sorted(unowned_teams))
            )
        return request_teams

    if not editable_team_names:
        raise ForbiddenError("You do not have any team to own the cloned recipe.")

    if common_teams := sorted(set(source_team_names) & set(editable_team_names)):
        return common_teams

    if len(editable_team_names) == 1:
        return editable_team_names

    raise BadRequestError(
        "You must select the teams that should own the cloned recipe."
    )


@router.post(
    "/{recipe_identifier}/clone",
    dependencies=[Depends(require_permission(namespace="recipes", name="create"))],
)
def clone_recipe(
    recipe_identifier: Annotated[NotEmptyString, Path()],
    request: CloneSchema,
    session: OrmSession = Depends(gen_dbsession),
    current_account: db_models.Account = Depends(get_current_account),
    viewable_team_ids: Sequence[UUID] | None = Depends(get_viewable_team_ids),
    editable_team_ids: Sequence[UUID] | None = Depends(get_editable_team_ids),
) -> RecipeCreateResponseSchema:
    recipe = db_recipe.get_recipe(
        session, recipe_identifier, accessible_team_ids=viewable_team_ids
    )
    if recipe.archived:
        raise BadRequestError("You cannot clone an archived recipe.")

    # Skip validation while cloning a recipe
    try:
        language = db_language.get_language_from_code(recipe.language_code)
    except RecordDoesNotExistError:
        language = LanguageSchema.model_validate(
            {"code": recipe.language_code, "name": recipe.language_code},
            context={"skip_validation": True},
        )
    offliner = db_offliner.get_offliner(
        session, recipe.config["offliner"]["offliner_id"]
    )
    offliner_definition = db_offliner_definition.create_offliner_definition_schema(
        recipe.offliner_definition
    )

    payload = db_recipe.RecipeCreateSchema(
        name=request.name,
        config=RecipeConfigSchema.model_validate(
            {
                **recipe.config,
                "offliner": db_offliner_definition.create_offliner_instance(
                    offliner=offliner,
                    offliner_definition=offliner_definition,
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
        comment=request.comment,
        teams=_resolve_clone_teams(
            session,
            request_teams=request.teams,
            source_team_names=[team_recipe.team.name for team_recipe in recipe.teams],
            editable_team_ids=editable_team_ids,
        ),
    )

    new_recipe = db_recipe.create_recipe(
        session,
        author_id=current_account.id,
        payload=payload,
        offliner_definition=offliner_definition,
        accessible_team_ids=editable_team_ids,
    )

    # validate the new recipe as we skipped validation to allow accounts clone
    # an invalid recipe. If validation fails, mark as invalid
    try:
        db_recipe.create_recipe_full_schema(new_recipe, offliner, skip_validation=False)
    except ValidationError:
        db_recipe.update_recipe(
            session,
            recipe_identifier=new_recipe.name,
            author_id=current_account.id,
            accessible_team_ids=editable_team_ids,
            payload=db_recipe.RecipeUpdateSchema(
                is_valid=False,
                offliner_definition=db_offliner_definition.create_offliner_definition_schema(
                    new_recipe.offliner_definition
                ),
            ),
        )

    return RecipeCreateResponseSchema(
        id=new_recipe.id,
    )


@router.patch(
    "/{recipe_identifier}/archive",
    dependencies=[Depends(require_permission(namespace="recipes", name="archive"))],
)
def archive_recipe(
    recipe_identifier: Annotated[NotEmptyString, Path()],
    request: ToggleArchiveStatusSchema,
    session: OrmSession = Depends(gen_dbsession),
    current_account: db_models.Account = Depends(get_current_account),
    accessible_team_ids: Sequence[UUID] | None = Depends(get_editable_team_ids),
) -> JSONResponse:
    """Archive a recipe"""
    db_recipe.toggle_archive_status(
        session,
        recipe_identifier=recipe_identifier,
        archived=True,
        actor_id=current_account.id,
        accessible_team_ids=accessible_team_ids,
        comment=request.comment,
    )
    return JSONResponse(
        content={"message": f"Recipe '{recipe_identifier}' has been archived"},
        status_code=HTTPStatus.OK,
    )


@router.patch(
    "/{recipe_identifier}/restore",
    dependencies=[Depends(require_permission(namespace="recipes", name="archive"))],
)
def restore_archived_recipe(
    recipe_identifier: Annotated[NotEmptyString, Path()],
    request: ToggleArchiveStatusSchema,
    session: OrmSession = Depends(gen_dbsession),
    current_account: db_models.Account = Depends(get_current_account),
    accessible_team_ids: Sequence[UUID] | None = Depends(get_editable_team_ids),
) -> JSONResponse:
    """Restore an archived recipe"""
    db_recipe.toggle_archive_status(
        session,
        recipe_identifier=recipe_identifier,
        archived=False,
        actor_id=current_account.id,
        accessible_team_ids=accessible_team_ids,
        comment=request.comment,
    )
    return JSONResponse(
        content={"message": f"Recipe '{recipe_identifier}' has been restored"},
        status_code=HTTPStatus.OK,
    )


@router.get(
    "/{recipe_identifier}/validate",
    dependencies=[Depends(require_permission(namespace="recipes", name="update"))],
)
def validate_recipe(
    recipe_identifier: Annotated[NotEmptyString, Path()],
    session: Annotated[OrmSession, Depends(gen_dbsession)],
    accessible_team_ids: Sequence[UUID] | None = Depends(get_editable_team_ids),
) -> JSONResponse:
    recipe = db_recipe.get_recipe(
        session, recipe_identifier, accessible_team_ids=accessible_team_ids
    )
    offliner = db_offliner.get_offliner(
        session, recipe.config["offliner"]["offliner_id"]
    )

    try:
        db_recipe.create_recipe_full_schema(recipe, offliner, skip_validation=False)
    except ValidationError as exc:
        raise RequestValidationError(exc.errors()) from exc

    return JSONResponse(content={"message": "Recipe validated with success"})


@router.get(
    "/{recipe_identifier}/history",
    dependencies=[Depends(require_permission(namespace="recipes", name="secrets"))],
)
def get_recipe_history(
    recipe_identifier: Annotated[NotEmptyString, Path()],
    session: OrmSession = Depends(gen_dbsession),
    accessible_team_ids: Sequence[UUID] | None = Depends(get_viewable_team_ids),
    skip: Annotated[SkipField, Query()] = 0,
    limit: Annotated[LimitFieldMax200, Query()] = 200,
) -> ListResponse[RecipeHistorySchema]:
    results = db_recipe.get_recipe_history(
        session,
        recipe_identifier=recipe_identifier,
        accessible_team_ids=accessible_team_ids,
        skip=skip,
        limit=limit,
    )
    return ListResponse(
        items=results.records,
        meta=calculate_pagination_metadata(
            nb_records=results.nb_records,
            skip=skip,
            limit=limit,
            page_size=len(results.records),
        ),
    )


@router.get(
    "/{recipe_identifier}/history/{history_id}",
    dependencies=[Depends(require_permission(namespace="recipes", name="secrets"))],
)
def get_recipe_history_entry(
    recipe_identifier: Annotated[NotEmptyString, Path()],
    history_id: Annotated[UUID, Path()],
    session: OrmSession = Depends(gen_dbsession),
    accessible_team_ids: Sequence[UUID] | None = Depends(get_viewable_team_ids),
) -> RecipeHistorySchema:
    history_entry = db_recipe.get_recipe_history_entry(
        session,
        recipe_identifier=recipe_identifier,
        history_id=history_id,
        accessible_team_ids=accessible_team_ids,
    )
    return db_recipe.create_recipe_history_schema(history_entry)


@router.patch(
    "/{recipe_identifier}/revert/{history_id}",
    dependencies=[Depends(require_permission(namespace="recipes", name="update"))],
)
def revert_recipe(
    recipe_identifier: Annotated[NotEmptyString, Path()],
    history_id: Annotated[UUID, Path()],
    request: RevertRecipeSchema,
    session: OrmSession = Depends(gen_dbsession),
    current_account: db_models.Account = Depends(get_current_account),
    accessible_team_ids: Sequence[UUID] | None = Depends(get_editable_team_ids),
) -> JSONResponse:
    """Revert a recipe to a previous history."""
    db_recipe.revert_recipe(
        session,
        recipe_identifier=recipe_identifier,
        history_id=history_id,
        author_id=current_account.id,
        accessible_team_ids=accessible_team_ids,
        comment=request.comment,
    )
    return JSONResponse(
        content={"message": f"Recipe '{recipe_identifier}' has been restored"},
        status_code=HTTPStatus.OK,
    )
