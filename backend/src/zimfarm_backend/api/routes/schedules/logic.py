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
    get_current_user,
    get_current_user_or_none,
)
from zimfarm_backend.api.routes.http_errors import (
    BadRequestError,
    NotFoundError,
    ServerError,
    UnauthorizedError,
)
from zimfarm_backend.api.routes.models import ListResponse
from zimfarm_backend.api.routes.schedules.models import (
    CloneSchema,
    RestoreSchedulesSchema,
    ScheduleCreateResponseSchema,
    ScheduleCreateSchema,
    SchedulesGetSchema,
    ScheduleUpdateSchema,
    ToggleArchiveStatusSchema,
)
from zimfarm_backend.api.routes.utils import get_schedule_image_tags
from zimfarm_backend.common.enums import (
    DockerImageName,
    ScheduleCategory,
    SchedulePeriodicity,
)
from zimfarm_backend.common.schemas.fields import (
    LimitFieldMax200,
    NotEmptyString,
    SkipField,
)
from zimfarm_backend.common.schemas.models import (
    LanguageSchema,
    ScheduleNotificationSchema,
    calculate_pagination_metadata,
)
from zimfarm_backend.common.schemas.orms import (
    OfflinerDefinitionSchema,
    ScheduleConfigSchema,
    ScheduleFullSchema,
    ScheduleHistorySchema,
    ScheduleLightSchema,
)
from zimfarm_backend.db.exceptions import (
    RecordDoesNotExistError,
)
from zimfarm_backend.db.language import get_language_from_code
from zimfarm_backend.db.models import User
from zimfarm_backend.db.offliner import get_offliner
from zimfarm_backend.db.offliner_definition import (
    create_offliner_definition_schema,
    create_offliner_instance,
    get_offliner_definition,
    get_offliner_definition_by_id,
)
from zimfarm_backend.db.schedule import create_schedule as db_create_schedule
from zimfarm_backend.db.schedule import (
    create_schedule_full_schema,
    create_schedule_history_schema,
    get_all_schedules,
)
from zimfarm_backend.db.schedule import delete_schedule as db_delete_schedule
from zimfarm_backend.db.schedule import get_schedule as db_get_schedule
from zimfarm_backend.db.schedule import get_schedule_history as db_get_schedule_history
from zimfarm_backend.db.schedule import (
    get_schedule_history_entry as db_get_schedule_history_entry,
)
from zimfarm_backend.db.schedule import get_schedules as db_get_schedules
from zimfarm_backend.db.schedule import (
    restore_schedules as db_restore_schedules,
)
from zimfarm_backend.db.schedule import (
    toggle_archive_status as db_toggle_archive_status,
)
from zimfarm_backend.db.schedule import update_schedule as db_update_schedule
from zimfarm_backend.db.user import check_user_permission
from zimfarm_backend.utils.offliners import (
    expanded_config,
    get_image_name,
    get_image_prefix,
    get_key_differences,
)

router = APIRouter(prefix="/schedules", tags=["schedules"])


@router.get("")
def get_schedules(
    params: Annotated[SchedulesGetSchema, Query()],
    session: OrmSession = Depends(gen_dbsession),
) -> ListResponse[ScheduleLightSchema]:
    results = db_get_schedules(
        session,
        skip=params.skip,
        limit=params.limit,
        lang=params.lang,
        categories=params.category,
        tags=params.tag,
        name=params.name,
        archived=params.archived,
    )
    return ListResponse(
        meta=calculate_pagination_metadata(
            nb_records=results.nb_records,
            skip=params.skip,
            limit=params.limit,
            page_size=len(results.schedules),
        ),
        items=cast(list[ScheduleLightSchema], results.schedules),
    )


@router.post("")
def create_schedule(
    request: ScheduleCreateSchema,
    session: OrmSession = Depends(gen_dbsession),
    current_user: User = Depends(get_current_user),
) -> JSONResponse:
    """Create a new schedule"""
    if not check_user_permission(current_user, namespace="schedules", name="create"):
        raise UnauthorizedError("You are not allowed to create a schedule")

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

    config = ScheduleConfigSchema.model_validate(
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

    db_schedule = db_create_schedule(
        session,
        author=current_user.username,
        name=request.name,
        offliner_definition=offliner_definition,
        category=ScheduleCategory(request.category),
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
        content=ScheduleCreateResponseSchema(
            id=db_schedule.id,
        ).model_dump(mode="json")
    )


@router.get("/backup")
def get_schedules_backup(
    session: OrmSession = Depends(gen_dbsession),
    current_user: User | None = Depends(get_current_user_or_none),
    *,
    hide_secrets: Annotated[bool | None, Query()] = True,
    archived: Annotated[bool, Query()] = False,
) -> JSONResponse:
    """Get a list of schedules"""
    if not (
        current_user
        and check_user_permission(current_user, namespace="schedules", name="secrets")
    ):
        exclude_notifications = True
    else:
        exclude_notifications = False

    # if the user doesn't have the appropriate permission, then their flag
    # does not matter
    if not (
        current_user
        and check_user_permission(current_user, namespace="schedules", name="secrets")
    ):
        show_secrets = False
    else:
        show_secrets = not hide_secrets

    results = get_all_schedules(session, archived=archived)
    schedules = cast(list[ScheduleFullSchema], results.schedules)
    content: list[dict[str, Any]] = []
    for schedule in schedules:
        if exclude_notifications:
            schedule.notification = None

        content.append(
            schedule.model_dump(mode="json", context={"show_secrets": show_secrets})
        )

    return JSONResponse(content=content)


@router.post("/restore")
def restore_archived_schedules(
    request: RestoreSchedulesSchema,
    session: OrmSession = Depends(gen_dbsession),
    current_user: User = Depends(get_current_user),
) -> Response:
    if not (
        current_user
        and check_user_permission(current_user, namespace="schedules", name="archive")
    ):
        raise UnauthorizedError("You are not allowed to restore schedules")

    db_restore_schedules(
        session,
        schedule_names=request.schedule_names,
        actor=current_user.username,
        comment=request.comment,
    )
    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.get("/{schedule_name}")
def get_schedule(
    schedule_name: Annotated[NotEmptyString, Path()],
    session: OrmSession = Depends(gen_dbsession),
    current_user: User | None = Depends(get_current_user_or_none),
    *,
    hide_secrets: Annotated[bool | None, Query()] = True,
) -> JSONResponse:
    db_schedule = db_get_schedule(session, schedule_name=schedule_name)

    if current_user is None and db_schedule.archived:
        raise UnauthorizedError(
            "You do not have permissions to view an archived schedule."
        )

    offliner = get_offliner(session, db_schedule.config["offliner"]["offliner_id"])

    try:
        schedule = create_schedule_full_schema(db_schedule, offliner)
    except Exception as exc:
        logger.exception("error retrieving schedule")
        raise exc
    offliner_definition = get_offliner_definition_by_id(
        session, db_schedule.offliner_definition_id
    )

    if not (
        current_user
        and check_user_permission(current_user, namespace="schedules", name="secrets")
    ):
        schedule.notification = None

    if not (
        current_user
        and check_user_permission(current_user, namespace="schedules", name="secrets")
    ):
        show_secrets = False
    else:
        show_secrets = not hide_secrets

    # validity field in DB might not reflect the actual validity of the schedule
    # as constraints evolve
    try:
        create_schedule_full_schema(db_schedule, offliner, skip_validation=False)
    except ValidationError:
        schedule.is_valid = False

    schedule.config = expanded_config(
        cast(ScheduleConfigSchema, schedule.config),
        offliner=offliner,
        offliner_definition=offliner_definition,
        show_secrets=show_secrets,
    )

    return JSONResponse(
        content=schedule.model_dump(mode="json", context={"show_secrets": show_secrets})
    )


@router.get("/{schedule_name}/similar")
def get_similar_schedule(
    schedule_name: Annotated[NotEmptyString, Path()],
    params: Annotated[SchedulesGetSchema, Query()],
    session: OrmSession = Depends(gen_dbsession),
) -> ListResponse[ScheduleLightSchema]:
    schedule = db_get_schedule(session, schedule_name=schedule_name)
    results = db_get_schedules(
        session,
        skip=params.skip,
        limit=params.limit,
        lang=params.lang,
        categories=params.category,
        tags=params.tag,
        archived=params.archived,
        similarity_data=schedule.similarity_data,
        omit_names=[schedule.name],
    )
    return ListResponse(
        meta=calculate_pagination_metadata(
            nb_records=results.nb_records,
            skip=params.skip,
            limit=params.limit,
            page_size=len(results.schedules),
        ),
        items=cast(list[ScheduleLightSchema], results.schedules),
    )


@router.patch("/{schedule_name}")
def update_schedule(
    schedule_name: Annotated[NotEmptyString, Path()],
    request: ScheduleUpdateSchema,
    session: OrmSession = Depends(gen_dbsession),
    current_user: User = Depends(get_current_user),
) -> JSONResponse:
    if not (
        current_user
        and check_user_permission(current_user, namespace="schedules", name="update")
    ):
        raise UnauthorizedError("You are not allowed to update a schedule")

    db_schedule = db_get_schedule(session, schedule_name=schedule_name)
    if db_schedule.archived:
        raise BadRequestError("Cannot update an archived schedule")
    offliner = get_offliner(session, db_schedule.config["offliner"]["offliner_id"])
    schedule = create_schedule_full_schema(db_schedule, offliner)

    schedule_config = cast(ScheduleConfigSchema, schedule.config)
    if not request.model_dump(exclude_unset=True):
        raise BadRequestError(
            "No changes were made to the schedule because no fields being set"
        )
    # track the defintion to be used for updating the schedule
    offliner_definition: OfflinerDefinitionSchema

    if (
        request.offliner
        and request.offliner
        != schedule_config.offliner.offliner_id  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType]
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

        # create a new schedule config for the new offliner validating the new flags
        new_schedule_config = ScheduleConfigSchema.model_validate(
            {
                # reuse the existing config except for the offliner and image
                **schedule_config.model_dump(
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
            new_schedule_config.offliner.model_dump(mode="json"),
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
                schedule_config.offliner.offliner_id,  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType]
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
            # Reuse the existing defintion to validate
            offliner_definition = get_offliner_definition_by_id(
                session, schedule.offliner_definition_id
            )

        new_schedule_config = ScheduleConfigSchema.model_validate(
            {
                **schedule_config.model_dump(
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
            new_schedule_config.offliner.model_dump(mode="json"),
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
        new_schedule_config = schedule_config
        offliner_definition = get_offliner_definition_by_id(
            session, schedule.offliner_definition_id
        )

    if request.image is not None:
        # Ensure the image for the offliner is a valid preset
        new_offliner_name = cast(
            str,
            new_schedule_config.offliner.offliner_id,  # pyright: ignore[reportAttributeAccessIssue,reportUnknownMemberType]
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

    # update the top-level schedule config attributes from the request but
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
    new_schedule_config = new_schedule_config.model_copy(update=update_data)

    if request.language:
        try:
            language = get_language_from_code(request.language)
        except RecordDoesNotExistError as exc:
            raise BadRequestError(
                f"Language code {request.language} not found."
            ) from exc
    else:
        language = None

    schedule = db_update_schedule(
        session,
        schedule_name=schedule_name,
        author=current_user.username,
        comment=request.comment,
        new_schedule_config=new_schedule_config,
        language=language,
        name=request.name,
        category=request.category,
        tags=request.tags,
        enabled=request.enabled,
        periodicity=request.periodicity,
        # schedule must be valid if it has not failed validation yet
        is_valid=True,
        context=request.context,
        offliner_definition=offliner_definition,
        notification=request.notification,
    )

    schedule = create_schedule_full_schema(schedule, offliner)
    schedule.config = expanded_config(
        cast(ScheduleConfigSchema, schedule.config),
        offliner=offliner,
        offliner_definition=offliner_definition,
        show_secrets=True,
    )
    return JSONResponse(
        content=schedule.model_dump(mode="json", context={"show_secrets": True})
    )


@router.delete("/{schedule_name}")
def delete_schedule(
    schedule_name: Annotated[NotEmptyString, Path()],
    session: OrmSession = Depends(gen_dbsession),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Delete a schedule"""
    if not (
        current_user
        and check_user_permission(current_user, namespace="schedules", name="delete")
    ):
        raise UnauthorizedError("You are not allowed to delete a schedule")

    db_delete_schedule(session, schedule_name=schedule_name)
    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.get("/{schedule_name}/image-names")
def get_schedule_image_names(
    schedule_name: Annotated[NotEmptyString, Path()],
    hub_name: Annotated[str, Query()],
    session: OrmSession = Depends(gen_dbsession),
) -> ListResponse[Any]:
    db_get_schedule(session, schedule_name=schedule_name)
    try:
        tags = get_schedule_image_tags(hub_name)
    except requests.HTTPError as exc:
        if exc.response.status_code == HTTPStatus.NOT_FOUND:
            raise NotFoundError("Image tags not found for schedule") from exc
        raise ServerError(
            "An unexpected error occured while fetching image tags: "
            f"{exc.response.reason}"
        ) from exc
    except requests.RequestException as exc:
        raise ServerError(
            "An unexpected error occured while fetching image tags: "
        ) from exc

    return ListResponse(
        items=tags,
        meta=calculate_pagination_metadata(
            nb_records=len(tags), skip=0, limit=len(tags), page_size=len(tags)
        ),
    )


@router.post("/{schedule_name}/clone")
def clone_schedule(
    schedule_name: Annotated[NotEmptyString, Path()],
    request: CloneSchema,
    session: OrmSession = Depends(gen_dbsession),
    current_user: User = Depends(get_current_user),
) -> ScheduleCreateResponseSchema:
    if not check_user_permission(current_user, namespace="schedules", name="create"):
        raise UnauthorizedError("You are not allowed to clone a schedule")

    schedule = db_get_schedule(session, schedule_name=schedule_name)
    if schedule.archived:
        raise BadRequestError("You cannot clone an archived schedule.")

    # Skip validation while cloning a schedule
    try:
        language = get_language_from_code(schedule.language_code)
    except RecordDoesNotExistError:
        language = LanguageSchema.model_validate(
            {"code": schedule.language_code, "name": schedule.language_code},
            context={"skip_validation": True},
        )
    offliner = get_offliner(session, schedule.config["offliner"]["offliner_id"])

    new_schedule = db_create_schedule(
        session,
        author=current_user.username,
        comment=request.comment,
        name=request.name,
        category=ScheduleCategory(schedule.category),
        config=ScheduleConfigSchema.model_validate(
            {
                **schedule.config,
                "offliner": create_offliner_instance(
                    offliner=offliner,
                    offliner_definition=create_offliner_definition_schema(
                        schedule.offliner_definition
                    ),
                    data=schedule.config["offliner"],
                    skip_validation=True,
                ),
            },
            context={"skip_validation": True},
        ),
        tags=schedule.tags,
        enabled=False,
        notification=(
            ScheduleNotificationSchema.model_validate(schedule.notification)
            if schedule.notification
            else None
        ),
        periodicity=SchedulePeriodicity(schedule.periodicity),
        language=language,
        context=schedule.context,
        offliner_definition=create_offliner_definition_schema(
            schedule.offliner_definition
        ),
    )

    # validate the new schedule as we skipped validation to allow users clone
    # an invalid schedule. If validation fails, mark as invalid
    try:
        create_schedule_full_schema(new_schedule, offliner, skip_validation=False)
    except ValidationError:
        db_update_schedule(
            session,
            schedule_name=new_schedule.name,
            author=current_user.username,
            is_valid=False,
            offliner_definition=create_offliner_definition_schema(
                new_schedule.offliner_definition
            ),
        )

    return ScheduleCreateResponseSchema(
        id=new_schedule.id,
    )


@router.patch("/{schedule_name}/archive")
def archive_schedule(
    schedule_name: Annotated[NotEmptyString, Path()],
    request: ToggleArchiveStatusSchema,
    session: OrmSession = Depends(gen_dbsession),
    current_user: User = Depends(get_current_user),
) -> JSONResponse:
    """Archive a schedule"""
    if not (
        current_user
        and check_user_permission(current_user, namespace="schedules", name="archive")
    ):
        raise UnauthorizedError("You are not allowed to archive a schedule")

    db_toggle_archive_status(
        session,
        schedule_name=schedule_name,
        archived=True,
        actor=current_user.username,
        comment=request.comment,
    )
    return JSONResponse(
        content={"message": f"Schedule '{schedule_name}' has been archived"},
        status_code=HTTPStatus.OK,
    )


@router.patch("/{schedule_name}/restore")
def restore_archived_schedule(
    schedule_name: Annotated[NotEmptyString, Path()],
    request: ToggleArchiveStatusSchema,
    session: OrmSession = Depends(gen_dbsession),
    current_user: User = Depends(get_current_user),
) -> JSONResponse:
    """Restore an archived schedule"""
    if not (
        current_user
        and check_user_permission(current_user, namespace="schedules", name="archive")
    ):
        raise UnauthorizedError("You are not allowed to restore a schedule")

    db_toggle_archive_status(
        session,
        schedule_name=schedule_name,
        archived=False,
        actor=current_user.username,
        comment=request.comment,
    )
    return JSONResponse(
        content={"message": f"Schedule '{schedule_name}' has been restored"},
        status_code=HTTPStatus.OK,
    )


@router.get("/{schedule_name}/validate")
def validate_schedule(
    schedule_name: Annotated[NotEmptyString, Path()],
    session: Annotated[OrmSession, Depends(gen_dbsession)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> JSONResponse:
    if not check_user_permission(current_user, namespace="schedules", name="update"):
        raise UnauthorizedError("You are not allowed to validate a schedule")

    schedule = db_get_schedule(session, schedule_name=schedule_name)
    offliner = get_offliner(session, schedule.config["offliner"]["offliner_id"])

    try:
        create_schedule_full_schema(schedule, offliner, skip_validation=False)
    except ValidationError as exc:
        raise RequestValidationError(exc.errors()) from exc

    return JSONResponse(content={"message": "Schedule validated with success"})


@router.get("/{schedule_name}/history")
def get_schedule_history(
    schedule_name: Annotated[NotEmptyString, Path()],
    session: OrmSession = Depends(gen_dbsession),
    current_user: User = Depends(get_current_user),
    skip: Annotated[SkipField, Query()] = 0,
    limit: Annotated[LimitFieldMax200, Query()] = 200,
) -> ListResponse[ScheduleHistorySchema]:
    if not check_user_permission(current_user, namespace="schedules", name="secrets"):
        raise UnauthorizedError("You are not allowed to view a schedule's history")

    schedule = db_get_schedule(session, schedule_name=schedule_name)

    results = db_get_schedule_history(
        session, schedule_id=schedule.id, skip=skip, limit=limit
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


@router.get("/{schedule_name}/history/{history_id}")
def get_schedule_history_entry(
    schedule_name: Annotated[NotEmptyString, Path()],
    history_id: Annotated[UUID, Path()],
    session: OrmSession = Depends(gen_dbsession),
    current_user: User = Depends(get_current_user),
) -> ScheduleHistorySchema:
    if not check_user_permission(current_user, namespace="schedules", name="secrets"):
        raise UnauthorizedError("You are not allowed to view a schedule's history")

    history_entry = db_get_schedule_history_entry(
        session, schedule_name=schedule_name, history_id=history_id
    )
    return create_schedule_history_schema(history_entry)
