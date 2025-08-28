from http import HTTPStatus
from typing import Annotated, Any, cast

import requests
from fastapi import APIRouter, Depends, Path, Query, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session as OrmSession

from zimfarm_backend.common.enums import Offliner, ScheduleCategory, SchedulePeriodicity
from zimfarm_backend.common.schemas.fields import ScheduleNameField
from zimfarm_backend.common.schemas.models import (
    LanguageSchema,
    ScheduleNotificationSchema,
    calculate_pagination_metadata,
)
from zimfarm_backend.common.schemas.orms import (
    ScheduleConfigSchema,
    ScheduleFullSchema,
    ScheduleLightSchema,
)
from zimfarm_backend.db.exceptions import (
    RecordAlreadyExistsError,
    RecordDoesNotExistError,
)
from zimfarm_backend.db.language import get_language_from_code
from zimfarm_backend.db.models import User
from zimfarm_backend.db.schedule import create_schedule as db_create_schedule
from zimfarm_backend.db.schedule import create_schedule_full_schema, get_all_schedules
from zimfarm_backend.db.schedule import delete_schedule as db_delete_schedule
from zimfarm_backend.db.schedule import get_schedule as db_get_schedule
from zimfarm_backend.db.schedule import get_schedules as db_get_schedules
from zimfarm_backend.db.schedule import update_schedule as db_update_schedule
from zimfarm_backend.db.user import check_user_permission
from zimfarm_backend.routes.dependencies import (
    gen_dbsession,
    get_current_user,
    get_current_user_or_none,
)
from zimfarm_backend.routes.http_errors import (
    BadRequestError,
    NotFoundError,
    ServerError,
    UnauthorizedError,
)
from zimfarm_backend.routes.models import ListResponse
from zimfarm_backend.routes.schedules.models import (
    CloneSchema,
    ScheduleCreateResponseSchema,
    ScheduleCreateSchema,
    SchedulesGetSchema,
    ScheduleUpdateSchema,
)
from zimfarm_backend.routes.utils import get_schedule_image_tags
from zimfarm_backend.utils.offliners import expanded_config, get_key_differences

router = APIRouter(prefix="/schedules", tags=["schedules"])


@router.get("")
def get_schedules(
    params: Annotated[SchedulesGetSchema, Query()],
    session: OrmSession = Depends(gen_dbsession),
) -> ListResponse[ScheduleLightSchema]:
    skip = params.skip if params.skip else 0
    limit = params.limit if params.limit else 20
    results = db_get_schedules(
        session,
        skip=skip,
        limit=limit,
        lang=params.lang,
        categories=params.category,
        tags=params.tag,
        name=params.name,
    )
    return ListResponse(
        meta=calculate_pagination_metadata(
            nb_records=results.nb_records,
            skip=skip,
            limit=limit,
            page_size=len(results.schedules),
        ),
        items=cast(list[ScheduleLightSchema], results.schedules),
    )


@router.post("")
def create_schedule(
    schedule: ScheduleCreateSchema,
    session: OrmSession = Depends(gen_dbsession),
    current_user: User = Depends(get_current_user),
) -> JSONResponse:
    """Create a new schedule"""
    if not check_user_permission(current_user, namespace="schedules", name="create"):
        raise UnauthorizedError("You are not allowed to create a schedule")

    try:
        config = ScheduleConfigSchema.model_validate(schedule.config)
    except ValidationError as exc:
        raise RequestValidationError(exc.errors()) from exc

    # We need to compare the raw offliner config with the validated offliner
    # config to ensure the caller didn't pass extra fields for the offliner config
    raw_offliner_config = schedule.config.get("offliner", {})
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

    try:
        language = get_language_from_code(schedule.language)
    except RecordDoesNotExistError as exc:
        raise BadRequestError(f"Language code {schedule.language} not found.") from exc

    try:
        db_schedule = db_create_schedule(
            session,
            name=schedule.name,
            category=ScheduleCategory(schedule.category),
            language=language,
            config=config,
            tags=schedule.tags,
            enabled=schedule.enabled,
            notification=schedule.notification,
            periodicity=schedule.periodicity,
        )
    except RecordAlreadyExistsError as exc:
        raise BadRequestError(f"Schedule {schedule.name} already exists") from exc

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
) -> JSONResponse:
    """Get a list of schedules"""
    if not (
        current_user
        and check_user_permission(current_user, namespace="schedules", name="update")
    ):
        exclude_notifications = True
    else:
        exclude_notifications = False

    # if the user doesn't have the appropriate permission, then their flag
    # does not matter
    if not (
        current_user
        and check_user_permission(current_user, namespace="schedules", name="update")
    ):
        show_secrets = False
    else:
        show_secrets = not hide_secrets

    results = get_all_schedules(session)
    schedules = cast(list[ScheduleFullSchema], results.schedules)
    content: list[dict[str, Any]] = []
    for schedule in schedules:
        if exclude_notifications:
            schedule.notification = None

        content.append(
            schedule.model_dump(mode="json", context={"show_secrets": show_secrets})
        )

    return JSONResponse(content=content)


@router.get("/{schedule_name}")
def get_schedule(
    schedule_name: Annotated[ScheduleNameField, Path()],
    session: OrmSession = Depends(gen_dbsession),
    current_user: User | None = Depends(get_current_user_or_none),
    *,
    hide_secrets: Annotated[bool | None, Query()] = True,
) -> JSONResponse:
    try:
        db_schedule = db_get_schedule(session, schedule_name=schedule_name)
    except RecordDoesNotExistError as e:
        raise NotFoundError(f"Schedule {schedule_name} not found") from e

    schedule = create_schedule_full_schema(db_schedule)
    if not (
        current_user
        and check_user_permission(current_user, namespace="schedules", name="update")
    ):
        schedule.notification = None

    if not (
        current_user
        and check_user_permission(current_user, namespace="schedules", name="update")
    ):
        show_secrets = False
    else:
        show_secrets = not hide_secrets

    # validity field in DB might not reflect the actual validity of the schedule
    # as constraints evolve
    try:
        create_schedule_full_schema(db_schedule, skip_validation=False)
    except ValidationError:
        schedule.is_valid = False

    schedule.config = expanded_config(
        cast(ScheduleConfigSchema, schedule.config), show_secrets=show_secrets
    )

    return JSONResponse(
        content=schedule.model_dump(mode="json", context={"show_secrets": show_secrets})
    )


@router.patch("/{schedule_name}")
def update_schedule(
    schedule_name: Annotated[ScheduleNameField, Path()],
    request: ScheduleUpdateSchema,
    session: OrmSession = Depends(gen_dbsession),
    current_user: User = Depends(get_current_user),
) -> JSONResponse:
    if not (
        current_user
        and check_user_permission(current_user, namespace="schedules", name="update")
    ):
        raise UnauthorizedError("You are not allowed to update a schedule")

    try:
        schedule = create_schedule_full_schema(
            db_get_schedule(session, schedule_name=schedule_name)
        )
    except RecordDoesNotExistError as e:
        raise NotFoundError(f"Schedule {schedule_name} not found") from e

    schedule_config = schedule.config
    # Ensure we test flags according to new offliner name if present
    if request.offliner and request.offliner != schedule_config.offliner.offliner_id:
        if request.flags is None:
            raise BadRequestError("Flags are required when changing offliner")

        if request.image is None:
            raise BadRequestError("Image is required when changing offliner")

        # determine if the caller passed extra fields for the new offliner config
        if request.flags:
            # Create a temporary config to get the new offliner schema for validation
            temp_config = ScheduleConfigSchema.model_validate(
                {
                    **schedule_config.model_dump(
                        mode="json",
                        exclude={"offliner", "image"},
                        context={"show_secrets": True},
                    ),
                    "offliner": {
                        "offliner_id": request.offliner,
                    },
                    "image": {
                        "name": request.image.name,
                        "tag": request.image.tag,
                    },
                }
            )
            if extra_keys := get_key_differences(
                request.flags,
                temp_config.offliner.model_dump(mode="json"),
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

        # create a new schedule config for the new offliner
        try:
            new_schedule_config = ScheduleConfigSchema.model_validate(
                {
                    # reuse the existing config except for the offliner and image
                    **schedule_config.model_dump(
                        mode="json",
                        exclude={"offliner", "image"},
                        context={"show_secrets": True},
                    ),
                    "offliner": {
                        "offliner_id": request.offliner,
                        **request.flags,
                    },
                    "image": {
                        "name": request.image.name,
                        "tag": request.image.tag,
                    },
                }
            )
        except ValidationError as exc:
            raise RequestValidationError(exc.errors()) from exc
    elif request.flags is not None:
        # determine if the caller passed extra fields for the existing offliner config
        if extra_keys := get_key_differences(
            request.flags,
            schedule_config.offliner.model_dump(mode="json"),
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
        # update the existing offliner flags
        try:
            new_schedule_config = ScheduleConfigSchema.model_validate(
                {
                    # reuse the existing config except for the offliner
                    **schedule_config.model_dump(
                        mode="json",
                        exclude={"offliner"},
                        context={"show_secrets": True},
                    ),
                    "offliner": {
                        "offliner_id": schedule_config.offliner.offliner_id,
                        # reuse the existing offliner flags and update with the new ones
                        **schedule_config.offliner.model_dump(
                            mode="json",
                            exclude={"offliner_id"},
                            context={"show_secrets": True},
                        ),
                        **request.flags,
                    },
                }
            )
        except ValidationError as exc:
            raise RequestValidationError(exc.errors()) from exc
    else:
        new_schedule_config = schedule_config

    if request.image is not None:
        # Ensure the image for the offliner is a valid preset
        new_offliner_name = Offliner(new_schedule_config.offliner.offliner_id)
        if Offliner.get_image_prefix(
            new_offliner_name
        ) + request.image.name != Offliner.get_image_name(new_offliner_name):
            raise BadRequestError("Image name must match selected offliner")

    # update the schedule config with attributes from the request
    new_schedule_config.warehouse_path = (
        request.warehouse_path or schedule_config.warehouse_path
    )
    new_schedule_config.resources = request.resources or schedule_config.resources
    new_schedule_config.platform = request.platform or schedule_config.platform
    new_schedule_config.artifacts_globs = (
        request.artifacts_globs or schedule_config.artifacts_globs
    )
    new_schedule_config.monitor = request.monitor or schedule_config.monitor

    new_schedule_config = cast(ScheduleConfigSchema, new_schedule_config)
    if request.language:
        try:
            language = get_language_from_code(request.language)
        except RecordDoesNotExistError as exc:
            raise BadRequestError(
                f"Language code {request.language} not found."
            ) from exc
    else:
        language = None

    try:
        schedule = db_update_schedule(
            session,
            schedule_name=schedule_name,
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
        )
    except RecordAlreadyExistsError as exc:
        raise BadRequestError(f"Schedule {request.name} already exists") from exc

    schedule = create_schedule_full_schema(schedule)
    schedule.config = expanded_config(cast(ScheduleConfigSchema, schedule.config))
    return JSONResponse(
        content=schedule.model_dump(mode="json", context={"show_secrets": True})
    )


@router.delete("/{schedule_name}")
def delete_schedule(
    schedule_name: Annotated[ScheduleNameField, Path()],
    session: OrmSession = Depends(gen_dbsession),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Delete a schedule"""
    if not (
        current_user
        and check_user_permission(current_user, namespace="schedules", name="delete")
    ):
        raise UnauthorizedError("You are not allowed to delete a schedule")

    try:
        db_delete_schedule(session, schedule_name=schedule_name)
    except RecordDoesNotExistError as e:
        raise NotFoundError(f"Schedule {schedule_name} not found") from e
    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.get("/{schedule_name}/image-names")
def get_schedule_image_names(
    schedule_name: Annotated[ScheduleNameField, Path()],
    hub_name: Annotated[str, Query()],
    session: OrmSession = Depends(gen_dbsession),
) -> ListResponse[Any]:
    try:
        db_get_schedule(session, schedule_name=schedule_name)
    except Exception as e:
        raise BadRequestError(f"Error getting schedule image names: {e}") from e

    try:
        tags = get_schedule_image_tags(hub_name)
    except requests.HTTPError as exc:
        if exc.response.status_code == HTTPStatus.NOT_FOUND:
            raise NotFoundError("Image tags not found for schedule") from exc
        raise ServerError(
            "An unexpected error occured while fetching image tags: "
            f"{exc.response.reason}"
        ) from exc
    return ListResponse(
        items=tags,
        meta=calculate_pagination_metadata(
            nb_records=len(tags), skip=0, limit=len(tags), page_size=len(tags)
        ),
    )


@router.post("/{schedule_name}/clone")
def clone_schedule(
    schedule_name: Annotated[ScheduleNameField, Path()],
    request: CloneSchema,
    session: OrmSession = Depends(gen_dbsession),
    current_user: User = Depends(get_current_user),
) -> ScheduleCreateResponseSchema:
    if not check_user_permission(current_user, namespace="schedules", name="create"):
        raise UnauthorizedError("You are not allowed to clone a schedule")

    try:
        schedule = db_get_schedule(session, schedule_name=schedule_name)
    except RecordDoesNotExistError as e:
        raise NotFoundError(f"Schedule {schedule_name} not found") from e

    # Skip validation while cloning a schedule
    try:
        language = get_language_from_code(schedule.language_code)
    except RecordDoesNotExistError:
        language = LanguageSchema.model_validate(
            {"code": schedule.language_code, "name": schedule.language_code},
            context={"skip_validation": True},
        )

    try:
        new_schedule = db_create_schedule(
            session,
            name=request.name,
            category=ScheduleCategory(schedule.category),
            config=ScheduleConfigSchema.model_validate(
                schedule.config, context={"skip_validation": True}
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
        )
    except RecordAlreadyExistsError as e:
        raise BadRequestError(f"Schedule {request.name} already exists") from e

    # validate the new schedule as we skipped validation to allow users clone
    # an invalid schedule. If validation fails, mark as invalid
    try:
        create_schedule_full_schema(new_schedule, skip_validation=False)
    except ValidationError:
        db_update_schedule(
            session,
            schedule_name=new_schedule.name,
            is_valid=False,
        )

    return ScheduleCreateResponseSchema(
        id=new_schedule.id,
    )


@router.get("/{schedule_name}/validate")
def validate_schedule(
    schedule_name: Annotated[ScheduleNameField, Path()],
    session: Annotated[OrmSession, Depends(gen_dbsession)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> JSONResponse:
    if not check_user_permission(current_user, namespace="schedules", name="update"):
        raise UnauthorizedError("You are not allowed to validate a schedule")

    try:
        schedule = db_get_schedule(session, schedule_name=schedule_name)
    except RecordDoesNotExistError as e:
        raise NotFoundError(f"Schedule {schedule_name} not found") from e

    try:
        create_schedule_full_schema(schedule, skip_validation=False)
    except ValidationError as exc:
        raise RequestValidationError(exc.errors()) from exc

    return JSONResponse(content={"message": "Schedule validated with success"})
