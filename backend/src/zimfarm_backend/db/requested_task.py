import datetime
from typing import cast
from uuid import UUID

from humanfriendly import format_size, format_timespan
from sqlalchemy import BigInteger, delete, func, or_, select, update
from sqlalchemy.orm import Session as OrmSession
from sqlalchemy.orm import selectinload

from zimfarm_backend import logger
from zimfarm_backend.common import getnow, to_naive_utc
from zimfarm_backend.common.constants import (
    ARTIFACTS_EXPIRATION,
    ARTIFACTS_UPLOAD_URI,
    DISABLE_WAREHOUSE_PATH,
    LOGS_EXPIRATION,
    LOGS_UPLOAD_URI,
    ZIM_EXPIRATION,
    ZIM_UPLOAD_URI,
    ZIMCHECK_OPTION,
    ZIMCHECK_RESULTS_EXPIRATION,
    ZIMCHECK_RESULTS_UPLOAD_URI,
)
from zimfarm_backend.common.enums import Platform, TaskStatus, WarehousePath
from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.common.schemas.models import (
    ExpandedRecipeConfigSchema,
    RecipeConfigSchema,
    RecipeNotificationSchema,
    ResourcesSchema,
)
from zimfarm_backend.common.schemas.orms import (
    BaseRequestedTaskSchema,
    ConfigResourcesSchema,
    ConfigWithOnlyOfflinerAndResourcesSchema,
    OfflinerDefinitionSchema,
    OfflinerSchema,
    RecipeDurationSchema,
    RequestedTaskFullSchema,
    RequestedTaskLightSchema,
    TaskUploadSchema,
    WorkerLightSchema,
)
from zimfarm_backend.db import count_from_stmt
from zimfarm_backend.db.exceptions import RecordDoesNotExistError
from zimfarm_backend.db.models import Recipe, RequestedTask, User, Worker
from zimfarm_backend.db.offliner import get_offliner
from zimfarm_backend.db.offliner_definition import (
    create_offliner_instance,
    get_offliner_definition_by_id,
)
from zimfarm_backend.db.recipe import get_recipe_duration, get_recipe_or_none
from zimfarm_backend.db.tasks import RunningTask, get_currently_running_tasks
from zimfarm_backend.db.worker import create_worker_schema, get_worker_or_none
from zimfarm_backend.utils.offliners import expanded_config
from zimfarm_backend.utils.timestamp import (
    get_status_timestamp_expr,
    get_timestamp_for_status,
)

# Maximum positive integer value for PostgreSQL BigInteger
MAX_BIG_INT_VAL = 2**63 - 1

RecipeOrTask = Recipe | RequestedTask


class RequestedTaskListResult(BaseModel):
    nb_records: int
    requested_tasks: list[RequestedTaskLightSchema]


class RequestedTaskWithDuration(BaseRequestedTaskSchema):
    duration: RecipeDurationSchema
    updated_at: datetime.datetime
    config: ExpandedRecipeConfigSchema


class RequestedTaskWithDurationResult(BaseModel):
    requested_task: RequestedTaskWithDuration | None
    error: str | None


class RequestTaskResult(BaseModel):
    requested_task: RequestedTaskFullSchema | None
    error: str | None


def _recipe_or_task_identifier_message(entity: RecipeOrTask):
    match entity:
        case Recipe():
            return f"recipe '{entity.name}'"
        case RequestedTask():
            return f"requested task '{entity.id}'"


def _resource_mismatch_message(
    worker: WorkerLightSchema, resource: ResourcesSchema
) -> list[str]:
    mismatched_message: list[str] = []
    if worker.resources.cpu < resource.cpu:
        mismatched_message.append(
            f"cpu: required={format_size(resource.cpu, binary=True)}, "
            f"available={format_size(worker.resources.cpu, binary=True)}"
        )

    if worker.resources.disk < resource.disk:
        mismatched_message.append(
            f"disk: required={format_size(resource.disk, binary=True)}, "
            f"available={format_size(worker.resources.disk, binary=True)}"
        )

    if worker.resources.memory < resource.memory:
        mismatched_message.append(
            f"memory: required={format_size(resource.memory, binary=True)}, "
            f"available={format_size(worker.resources.memory, binary=True)}"
        )
    return mismatched_message


def _create_new_requested_task(
    session: OrmSession,
    *,
    requested_by: UUID,
    recipe: Recipe,
    offliner: OfflinerSchema,
    offliner_definition: OfflinerDefinitionSchema,
    worker: WorkerLightSchema | None,
    priority: int = 0,
):
    """Create a new requested task."""
    now = getnow()
    requested_task = RequestedTask(
        status=TaskStatus.requested,
        timestamp=[(TaskStatus.requested.value, now)],
        events=[{"code": TaskStatus.requested, "timestamp": now}],
        priority=priority,
        config=expanded_config(
            offliner=offliner,
            offliner_definition=offliner_definition,
            config=RecipeConfigSchema.model_validate(
                {
                    **recipe.config,
                    "warehouse_path": (
                        WarehousePath.root
                        if DISABLE_WAREHOUSE_PATH
                        else recipe.config["warehouse_path"]
                    ),
                    "offliner": create_offliner_instance(
                        offliner=offliner,
                        offliner_definition=offliner_definition,
                        data=recipe.config["offliner"],
                        skip_validation=False,
                    ),
                }
            ),
        ).model_dump(mode="json", context={"show_secrets": True}),
        upload={
            "zim": {
                "upload_uri": ZIM_UPLOAD_URI,
                "expiration": ZIM_EXPIRATION,
                "zimcheck": ZIMCHECK_OPTION,
                "disable_warehouse_path": DISABLE_WAREHOUSE_PATH,
            },
            "logs": {
                "upload_uri": LOGS_UPLOAD_URI,
                "expiration": LOGS_EXPIRATION,
            },
            "artifacts": {
                "upload_uri": ARTIFACTS_UPLOAD_URI,
                "expiration": ARTIFACTS_EXPIRATION,
            },
            "check": {
                "upload_uri": ZIMCHECK_RESULTS_UPLOAD_URI,
                "expiration": ZIMCHECK_RESULTS_EXPIRATION,
            },
        },
        notification=recipe.notification if recipe.notification else {},
        updated_at=now,
        original_recipe_name=recipe.name,
        # Track the worker context requirement for this recipe (from the recipe)
        # as recipe might be deleted from DB
        context=recipe.context,
    )
    requested_task.requested_by_id = requested_by
    requested_task.recipe = recipe
    if worker:
        requested_task.worker_id = worker.id
    requested_task.offliner_definition = recipe.offliner_definition

    session.add(requested_task)
    session.flush()
    return requested_task


def _validate_recipe_request_uniqueness(
    session: OrmSession, *, recipe_name: str, worker_name: str | None
):
    query = (
        select(RequestedTask, Recipe)
        .join(Recipe, RequestedTask.recipe)
        .where(Recipe.name == recipe_name)
    )
    if worker_name is not None:
        query = query.join(Worker, RequestedTask.worker).where(
            Worker.name == worker_name
        )

    if count_from_stmt(session, query) > 0:
        return f"Recipe '{recipe_name}' already requested"
    return None


def _validate_recipe_state(
    session: OrmSession, recipe_name: str
) -> tuple[Recipe | None, str | None]:
    recipe = get_recipe_or_none(session, recipe_name=recipe_name)
    if recipe is None or not recipe.enabled:
        return None, f"Recipe '{recipe_name}' not found or disabled"
    if recipe.archived:
        return None, f"Recipe '{recipe_name}' is archived"
    return recipe, None


def _validate_worker_context(
    worker: WorkerLightSchema, entity: RecipeOrTask
) -> str | None:
    if not entity.context:
        return None
    identifier = _recipe_or_task_identifier_message(entity)
    if entity.context not in worker.contexts:
        return (
            f"Worker '{worker.name}' does not have required context to run "
            f"{identifier}."
        )

    allowed_ip = worker.contexts[entity.context]
    if allowed_ip is not None and str(allowed_ip) != str(worker.last_ip):
        return (
            f"Worker '{worker.name}' has required context but IP is not whitelisted "
            "to run {identifier}."
        )
    return None


def _validate_worker_offliner(
    worker: WorkerLightSchema, entity: RecipeOrTask
) -> str | None:
    identifier = _recipe_or_task_identifier_message(entity)
    if entity.config["offliner"]["offliner_id"] not in worker.offliners:
        return (
            f"Worker '{worker.name}' offliners do not match the offliner for "
            f"{identifier} "
        )
    return None


def _validate_worker_availability(worker: WorkerLightSchema) -> str | None:
    if worker.cordoned or worker.admin_disabled:
        return f"Worker '{worker.name}' is cordoned/disabled."
    return None


def _validate_worker_resources(
    worker: WorkerLightSchema, entity: RecipeOrTask
) -> str | None:
    identifier = _recipe_or_task_identifier_message(entity)
    resource = ResourcesSchema.model_validate(entity.config["resources"])
    if (
        worker.resources.cpu < resource.cpu
        or worker.resources.memory < resource.memory
        or worker.resources.disk < resource.disk
    ):
        mismatched_message = _resource_mismatch_message(worker, resource)
        return (
            f"Worker '{worker.name}' does not have enough resources to run "
            f"{identifier}. Insufficient: {'; '.join(mismatched_message)}"
        )
    return None


def request_task(
    session: OrmSession,
    *,
    recipe_name: str,
    requested_by: UUID,
    worker_name: str | None = None,
    priority: int = 0,
) -> RequestTaskResult:
    """Request a task for the given recipe name if possible else None

    Recipe can't be requested if already requested on same worker.
    Recipe can't be requested if it's disabled.
    Recipe can't be requested if worker does not have appropriate context.
    """

    if error := _validate_recipe_request_uniqueness(
        session, recipe_name=recipe_name, worker_name=worker_name
    ):
        return RequestTaskResult(requested_task=None, error=error)

    recipe, error = _validate_recipe_state(session, recipe_name)
    if recipe is None:
        return RequestTaskResult(requested_task=None, error=error)

    worker: WorkerLightSchema | None = None
    if worker_name is not None:
        db_worker = get_worker_or_none(session, worker_name=worker_name)
        if db_worker is None:
            return RequestTaskResult(
                requested_task=None, error=f"Worker '{worker_name}' not found"
            )
        worker = create_worker_schema(db_worker)
        if error := _validate_worker_availability(worker):
            return RequestTaskResult(requested_task=None, error=error)

        for validator in (
            _validate_worker_context,
            _validate_worker_offliner,
            _validate_worker_resources,
        ):
            if error := validator(worker, recipe):
                return RequestTaskResult(requested_task=None, error=error)

    offliner_definition = get_offliner_definition_by_id(
        session, recipe.offliner_definition_id
    )
    offliner = get_offliner(session, offliner_definition.offliner)

    # Otherwise, create a new requested task
    requested_task = _create_new_requested_task(
        session,
        requested_by=requested_by,
        recipe=recipe,
        offliner=offliner,
        offliner_definition=offliner_definition,
        worker=worker,
        priority=priority,
    )

    return RequestTaskResult(
        requested_task=create_requested_task_full_schema(session, requested_task),
        error=None,
    )


def get_requested_tasks(
    session: OrmSession,
    *,
    worker_name: str | None = None,
    skip: int,
    limit: int,
    matching_offliners: list[str] | None = None,
    recipe_name: list[str] | None = None,
    priority: int | None = None,
    cpu: int | None = None,
    memory: int | None = None,
    disk: int | None = None,
) -> RequestedTaskListResult:
    """Get a paginated list of requested tasks filtered by various criteria.

    Tasks are sorted by priority (descending), reserved timestamp, and
    requested timestamp.
    """
    # Set reasonable defaults if a client omits a param
    priority = priority or 0
    cpu = cpu if cpu is not None else MAX_BIG_INT_VAL
    memory = memory if memory is not None else MAX_BIG_INT_VAL
    disk = disk if disk is not None else MAX_BIG_INT_VAL

    query = (
        select(
            func.count().over().label("nb_records"),
            RequestedTask.id,
            RequestedTask.status,
            RequestedTask.config,
            RequestedTask.timestamp,
            User.display_name.label("requested_by"),
            User.id.label("requester_id"),
            RequestedTask.priority,
            RequestedTask.original_recipe_name,
            RequestedTask.updated_at,
            RequestedTask.context,
            Recipe.name.label("recipe_name"),
            Worker.name.label("worker_name"),
        )
        .join(User, RequestedTask.requested_by)
        .join(Worker, RequestedTask.worker, isouter=True)
        .join(Recipe, RequestedTask.recipe, isouter=True)
        .where(
            # If a client provides an argument i.e it is not None, we compare the
            # corresponding model field against the argument, otherwise, we compare the
            # argument to its default in param which translates to a SQL true i.e
            # we don't filter based on this argument.
            (Recipe.name.in_(recipe_name or [])) | (recipe_name is None),
            (RequestedTask.priority >= priority),
            (RequestedTask.config["resources"]["cpu"].astext.cast(BigInteger) <= cpu),
            (
                RequestedTask.config["resources"]["memory"].astext.cast(BigInteger)
                <= memory
            ),
            (RequestedTask.config["resources"]["disk"].astext.cast(BigInteger) <= disk),
            (
                RequestedTask.config["offliner"]["offliner_id"].astext.in_(
                    matching_offliners or []
                )
                | (matching_offliners is None)
            ),
            (Worker.name == worker_name)
            | (
                RequestedTask.worker is None
            )  # pyright: ignore[reportUnnecessaryComparison]
            | (worker_name is None),
        )
        .order_by(
            RequestedTask.priority.desc(),
            get_status_timestamp_expr(
                RequestedTask.timestamp, TaskStatus.requested
            ).desc(),
        )
    )

    query = query.offset(skip).limit(limit)

    results = RequestedTaskListResult(nb_records=0, requested_tasks=[])

    for (
        nb_records,
        requested_task_id,
        status,
        config,
        timestamp,
        requested_by,
        requester_id,
        _priority,
        original_recipe_name,
        updated_at,
        context,
        _recipe_name,
        _worker_name,
    ) in session.execute(query).all():
        # Because the SQL window function returns the total_records
        # for every row, assign that value to the nb_records
        results.nb_records = nb_records
        results.requested_tasks.append(
            RequestedTaskLightSchema(
                id=requested_task_id,
                status=status,
                config=ConfigWithOnlyOfflinerAndResourcesSchema(
                    offliner=config["offliner"]["offliner_id"],
                    resources=ConfigResourcesSchema(
                        cpu=config["resources"]["cpu"],
                        memory=config["resources"]["memory"],
                        disk=config["resources"]["disk"],
                    ),
                ),
                timestamp=timestamp,
                requested_by=requested_by,
                requester_id=requester_id,
                priority=_priority,
                original_recipe_name=original_recipe_name,
                original_schedule_name=original_recipe_name,
                updated_at=updated_at,
                worker_name=_worker_name,
                recipe_name=_recipe_name,
                schedule_name=_recipe_name,
                context=context,
            )
        )

    return results


def create_requested_task_with_duration(
    session: OrmSession, *, task: RequestedTask, worker: WorkerLightSchema
) -> RequestedTaskWithDuration:
    return RequestedTaskWithDuration(
        id=task.id,
        status=task.status,
        schedule_name=task.recipe.name if task.recipe else None,
        original_schedule_name=task.original_recipe_name,
        recipe_name=task.recipe.name if task.recipe else None,
        original_recipe_name=task.original_recipe_name,
        config=ExpandedRecipeConfigSchema.model_validate(
            {
                **task.config,
                "offliner": create_offliner_instance(
                    offliner=get_offliner(session, task.offliner_definition.offliner),
                    offliner_definition=task.offliner_definition,
                    data=task.config["offliner"],
                    skip_validation=True,
                ),
            },
            context={"skip_validation": True},
        ),
        timestamp=task.timestamp,
        requested_by=task.requested_by.display_name,
        requester_id=task.requested_by.id,
        priority=task.priority,
        worker_name=task.worker.name if task.worker else worker.name,
        context=task.context,
        duration=get_recipe_duration(
            session,
            recipe_name=task.recipe.name if task.recipe else None,
            worker_name=worker.name,
        ),
        updated_at=task.updated_at,
    )


def get_tasks_doable_by_worker(
    session: OrmSession,
    worker: WorkerLightSchema,
    requested_task_id: UUID | None = None,
) -> list[RequestedTaskWithDuration]:
    """list of tasks that a worker can do with its total resources.

    The tasks are sorted by:
    - priority
    - duration (longest first)
    - requested_at (oldest first)
    """

    if worker.cordoned or worker.admin_disabled:
        return []

    def filter_req_task_for_ip_issues(task: RequestedTask):
        """Filter out tasks where worker IP doesn't match the context requirement"""
        return bool(
            # task has no context
            task.context == ""
            # context is not requiring a specific worker IP
            or worker.contexts.get(task.context) is None
            # worker IP is still matching the IP whitelisted for this context
            or worker.contexts[task.context] == worker.last_ip
        )

    query = (
        select(RequestedTask)
        .options(
            selectinload(RequestedTask.offliner_definition),
            selectinload(RequestedTask.requested_by),
        )
        .where(
            RequestedTask.config["resources"]["cpu"].astext.cast(BigInteger)
            <= worker.resources.cpu,
            RequestedTask.config["resources"]["memory"].astext.cast(BigInteger)
            <= worker.resources.memory,
            RequestedTask.config["resources"]["disk"].astext.cast(BigInteger)
            <= worker.resources.disk,
            RequestedTask.config["offliner"]["offliner_id"].astext.in_(
                worker.offliners
            ),
            (RequestedTask.id == requested_task_id) | (requested_task_id is None),
            # if requested task has a context, worker must have that context
            or_(
                # if a task has a context set to empty string, it should be
                # considered
                RequestedTask.context == "",
                RequestedTask.context.in_(worker.contexts.keys()),
            ),
        )
    )
    if worker.selfish:
        query = query.where(RequestedTask.worker_id == worker.id)
    else:
        query = query.where(
            or_(
                RequestedTask.worker_id == worker.id,
                RequestedTask.worker_id.is_(None),
            )
        )

    return sorted(
        [
            create_requested_task_with_duration(session, task=task, worker=worker)
            for task in filter(filter_req_task_for_ip_issues, session.scalars(query))
        ],
        key=lambda x: (-x.priority, -x.duration.value, x.updated_at),
    )


def does_platform_allow_worker_to_run(
    *,
    worker: WorkerLightSchema,
    all_running_tasks: list[RunningTask],
    running_tasks: list[RunningTask],
    task: RequestedTaskWithDuration,
) -> tuple[bool, str | None]:
    """check if a worker can run a task based on its platform limitations"""
    platform = cast(
        str,
        task.config.offliner.offliner_id,  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType]
    )
    if not platform:
        return True, None

    # check whether we have an overall per-platform limit
    platform_overall_limit = Platform.get_max_overall_tasks_for(platform)
    if platform_overall_limit is not None:
        nb_platform_running = sum(
            [
                1
                for running_task in all_running_tasks
                if running_task.config.offliner.offliner_id  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType]
                == platform
            ]
        )
        if nb_platform_running >= platform_overall_limit:
            return False, (
                f"Platform '{platform}' overall limits exceeded; "
                f"currently running {nb_platform_running} out "
                f"of {platform_overall_limit} tasks."
            )

    # check whether we have a per-worker limit for this platform
    worker_limit = worker.platforms.get(
        platform, Platform.get_max_per_worker_tasks_for(platform)
    )
    if worker_limit is None:
        return True, None

    nb_worker_running = sum(
        [
            1
            for running_task in running_tasks
            if running_task.config.offliner.offliner_id  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType]
            == platform
        ]
    )
    if nb_worker_running < worker_limit:
        return True, None
    return False, (
        f"Worker '{worker.name} limit for platform '{platform}' exceeded; "
        f"currently running {nb_worker_running} out "
        f"of {worker_limit} tasks."
    )


def get_possible_task_with_resources(
    *,
    tasks_worker_could_do: list[RequestedTaskWithDuration],
    available_resources: ResourcesSchema,
    available_time: float,
) -> RequestedTaskWithDuration | None:
    """first of possible tasks runnable with availresources within avail_time"""
    for temp_candidate in tasks_worker_could_do:
        if _can_run(temp_candidate, available_resources):
            if temp_candidate.duration.value <= available_time:
                logger.debug(f"{temp_candidate.id}@{temp_candidate.recipe_name} it is!")
                return temp_candidate
            logger.debug(
                f"{temp_candidate.id}@{temp_candidate.recipe_name} would take too long"
            )
    return None


def _can_run(task: RequestedTaskWithDuration, resource: ResourcesSchema) -> bool:
    """whether resources are suffiscient to run this task"""
    if (
        task.config.resources.cpu > resource.cpu
        or task.config.resources.memory > resource.memory
        or task.config.resources.disk > resource.disk
    ):
        return False
    return True


def _get_worker_unavailable_reason(
    worker: WorkerLightSchema, running_tasks: list[RunningTask]
) -> str:
    running_task_timestamps = [
        get_timestamp_for_status(
            t.timestamp,
            status=TaskStatus.reserved,
        )
        for t in running_tasks
    ]

    last_seen_reason = ""
    if worker.last_seen:
        last_seen_reason = (
            " and was last seen "
            f"{format_timespan((getnow() - worker.last_seen).total_seconds())} ago"
        )

    if running_task_timestamps:
        elapsed_seconds = int(
            (getnow() - to_naive_utc(max(running_task_timestamps))).total_seconds()
        )
        reason = (
            f"We have no reason for this task to not start on worker '{worker.name}' "
            "but workers do start only one task at a time and last task started "
            f"{format_timespan(elapsed_seconds)} ago. Worker is {worker.status}"
        ) + last_seen_reason
        return reason

    if worker.status == "offline":
        reason = f"Worker '{worker.name}' appears to be offline " + last_seen_reason
        return reason

    return (
        f"We have no reason for this task to not start on worker '{worker.name}' as "
        f"worker has no running tasks. Worker is {worker.status}"
    ) + last_seen_reason


def diagnose_requested_task(
    session: OrmSession,
    *,
    worker: WorkerLightSchema,
    requested_task: RequestedTask,
) -> str:
    """Diagnose why a requested task isn't running on worker"""
    if reason := _validate_worker_availability(worker):
        return reason

    for validator in (
        _validate_worker_context,
        _validate_worker_offliner,
        _validate_worker_resources,
    ):
        if reason := validator(worker, requested_task):
            return reason

    if worker.selfish:
        if requested_task.worker_id != worker.id:
            return f"Worker '{worker.name}' is selfish and cannot run task."
    elif requested_task.worker_id and requested_task.worker_id != worker.id:
        return f"Task is assigned to a different worker '{requested_task.worker.name}'."  # pyright: ignore[reportOptionalMemberAccess]

    # retrieve list of all running tasks with associated resources
    all_running_tasks = get_currently_running_tasks(session)
    # retrieve list of tasks we are currently running on worker
    running_tasks = [
        task for task in all_running_tasks if task.worker_name == worker.name
    ]

    task = create_requested_task_with_duration(
        session, task=requested_task, worker=worker
    )

    if reason := does_platform_allow_worker_to_run(
        worker=worker,
        all_running_tasks=all_running_tasks,
        running_tasks=running_tasks,
        task=task,
    )[1]:
        return reason

    available_resources = ResourcesSchema(
        cpu=worker.resources.cpu,
        memory=worker.resources.memory,
        disk=worker.resources.disk,
    )

    if _can_run(task, available_resources):
        return _get_worker_unavailable_reason(worker, running_tasks)

    # Calculate when resources will become available
    if reason := _find_task_that_can_run_with_available_resources(
        worker=worker,
        candidates=[task],
        available_resources=available_resources,
        missing_resources=ResourcesSchema(
            cpu=max([task.config.resources.cpu - available_resources.cpu, 0]),
            memory=max([task.config.resources.memory - available_resources.memory, 0]),
            disk=max([task.config.resources.disk - available_resources.disk, 0]),
        ),
        running_tasks=running_tasks,
    ).error:
        return reason

    return _get_worker_unavailable_reason(worker, running_tasks=running_tasks)


def _find_task_that_can_run_with_available_resources(
    *,
    worker: WorkerLightSchema,
    candidates: list[RequestedTaskWithDuration],
    available_resources: ResourcesSchema,
    missing_resources: ResourcesSchema,
    running_tasks: list[RunningTask],
) -> RequestedTaskWithDurationResult:
    logger.debug(
        f"missing cpu:{missing_resources.cpu}, mem:{missing_resources.memory}, "
        f"disk:{missing_resources.disk}"
    )
    # pile-up all of those which we need to complete to have enough resources
    preventing_tasks: list[RunningTask] = []
    for task in sorted(running_tasks, key=lambda x: x.eta):
        preventing_tasks.append(task)
        if (
            sum([t.config.resources.cpu for t in preventing_tasks])
            >= missing_resources.cpu
            and sum([t.config.resources.memory for t in preventing_tasks])
            >= missing_resources.memory
            and sum([t.config.resources.disk for t in preventing_tasks])
            >= missing_resources.disk
        ):
            # stop when we'd have reclaimed our missing resources
            break

    if not preventing_tasks:
        # we should not get there: no preventing task yet we don't have our total
        return RequestedTaskWithDurationResult(
            requested_task=None,
            error=(
                f"We have no preventing tasks. Perhaps worker '{worker.name}' isn't "
                "online or hasn't polled for task."
            ),
        )

    logger.debug(f"we have {len(preventing_tasks)} tasks blocking out way")
    opening_eta = preventing_tasks[-1].eta
    logger.debug(f"opening_eta:{opening_eta}")

    # get the number of available seconds from now to that ETA
    available_time = (opening_eta - getnow()).total_seconds()
    logger.debug(f"we have approx. {available_time / 60} minutes to reclaim resources")

    # loop on task[1+] to find the first task which can fit
    temp_candidate = get_possible_task_with_resources(
        tasks_worker_could_do=candidates,
        available_resources=available_resources,
        available_time=available_time,
    )
    if temp_candidate:
        return RequestedTaskWithDurationResult(
            requested_task=temp_candidate, error=None
        )

    # if none in the loop are possible, return None (worker will wait)
    return RequestedTaskWithDurationResult(
        requested_task=None,
        error=(
            f"Worker '{worker.name}' has too many tasks running. We have approx. "
            f"{available_time / 60} minutes to reclaim resources. Unable to fit "
            "anything, you'll have to wait for task(s) to complete."
        ),
    )


def find_requested_task_for_worker(
    session: OrmSession,
    *,
    worker: WorkerLightSchema,
    avail_cpu: int,
    avail_memory: int,
    avail_disk: int,
) -> RequestedTaskWithDurationResult:
    """Find optimal task to run for a given worker with given resources.

    The optimal task is the one that will finish the soonest.
    - If there are multiple tasks that finish at the same time, the one with the highest
    priority is chosen.
    - If there are multiple tasks with the same priority, the one with the lowest id
    is chosen.
    """

    if error := _validate_worker_availability(worker):
        return RequestedTaskWithDurationResult(requested_task=None, error=error)

    # retrieve list of all running tasks with associated resources
    all_running_tasks = get_currently_running_tasks(session)
    # retrieve list of tasks we are currently running on worker
    running_tasks = [
        task for task in all_running_tasks if task.worker_name == worker.name
    ]

    # filter-out requested tasks that are not doable now due to platform limitations
    tasks_worker_could_do = (
        task
        for task in get_tasks_doable_by_worker(session=session, worker=worker)
        if does_platform_allow_worker_to_run(
            worker=worker,
            all_running_tasks=all_running_tasks,
            running_tasks=running_tasks,
            task=task,
        )[0]
    )

    candidate = next(tasks_worker_could_do, None)
    if candidate is None:
        return RequestedTaskWithDurationResult(
            requested_task=None,
            error="Worker has exceeded platform limits for offliner",
        )
        return None

    available_resources = ResourcesSchema(
        cpu=avail_cpu,
        memory=avail_memory,
        disk=avail_disk,
    )

    if _can_run(candidate, available_resources):
        logger.debug("first candidate can be run!")
        return RequestedTaskWithDurationResult(requested_task=candidate, error=None)

    return _find_task_that_can_run_with_available_resources(
        worker=worker,
        candidates=list(tasks_worker_could_do),
        available_resources=available_resources,
        missing_resources=ResourcesSchema(
            cpu=max([candidate.config.resources.cpu - avail_cpu, 0]),
            memory=max([candidate.config.resources.memory - avail_memory, 0]),
            disk=max([candidate.config.resources.disk - avail_disk, 0]),
        ),
        running_tasks=running_tasks,
    )


def create_requested_task_full_schema(
    session: OrmSession, requested_task: RequestedTask
) -> RequestedTaskFullSchema:
    return RequestedTaskFullSchema(
        id=requested_task.id,
        status=requested_task.status,
        config=ExpandedRecipeConfigSchema.model_validate(
            {
                **requested_task.config,
                "offliner": create_offliner_instance(
                    offliner=get_offliner(
                        session, requested_task.offliner_definition.offliner
                    ),
                    offliner_definition=requested_task.offliner_definition,
                    data=requested_task.config["offliner"],
                    skip_validation=True,
                ),
            },
            context={"skip_validation": True},
        ),
        timestamp=requested_task.timestamp,
        requested_by=requested_task.requested_by.display_name,
        requester_id=requested_task.requested_by.id,
        priority=requested_task.priority,
        recipe_name=(requested_task.recipe.name if requested_task.recipe else None),
        schedule_name=(requested_task.recipe.name if requested_task.recipe else None),
        original_recipe_name=requested_task.original_recipe_name,
        original_schedule_name=requested_task.original_recipe_name,
        worker_name=requested_task.worker.name if requested_task.worker else None,
        context=requested_task.context,
        events=requested_task.events,
        upload=TaskUploadSchema.model_validate(requested_task.upload),
        notification=(
            RecipeNotificationSchema.model_validate(requested_task.notification)
            if requested_task.notification
            else None
        ),
        rank=compute_requested_task_rank(session, requested_task.id),
        updated_at=requested_task.updated_at,
        recipe_id=requested_task.recipe_id,
        offliner_definition_id=requested_task.offliner_definition_id,
        version=requested_task.offliner_definition.version,
        offliner=requested_task.offliner_definition.offliner,
    )


def get_raw_requested_task_or_none(
    session: OrmSession, requested_task_id: UUID
) -> RequestedTask | None:
    return session.scalars(
        select(RequestedTask)
        .options(
            selectinload(RequestedTask.offliner_definition),
            selectinload(RequestedTask.requested_by),
        )
        .where(RequestedTask.id == requested_task_id)
    ).one_or_none()


def get_requested_task_by_id_or_none(
    session: OrmSession, requested_task_id: UUID
) -> RequestedTaskFullSchema | None:
    if requested_task := get_raw_requested_task_or_none(session, requested_task_id):
        return create_requested_task_full_schema(session, requested_task)
    return None


def get_raw_requested_task(
    session: OrmSession, requested_task_id: UUID
) -> RequestedTask:
    requested_task = get_raw_requested_task_or_none(session, requested_task_id)
    if requested_task is None:
        raise RecordDoesNotExistError(f"Requested task {requested_task_id} not found")
    return requested_task


def get_requested_task_by_id(
    session: OrmSession, requested_task_id: UUID
) -> RequestedTaskFullSchema:
    return create_requested_task_full_schema(
        session, get_raw_requested_task(session, requested_task_id)
    )


def compute_requested_task_rank(session: OrmSession, requested_task_id: UUID) -> int:
    """Compute the rank of a requested task based on its priority and updated_at."""
    stmt = select(RequestedTask.id).order_by(
        RequestedTask.priority.desc(), RequestedTask.updated_at.asc()
    )
    return session.scalars(stmt).all().index(requested_task_id)


def update_requested_task_priority(
    session: OrmSession, requested_task_id: UUID, priority: int
) -> RequestedTaskFullSchema:
    """Update the priority of a requested task."""
    requested_task = session.scalars(
        update(RequestedTask)
        .where(RequestedTask.id == requested_task_id)
        .values(priority=priority)
        .returning(RequestedTask)
    ).one()
    return create_requested_task_full_schema(session, requested_task)


def delete_requested_task(session: OrmSession, requested_task_id: UUID) -> None:
    """Delete a requested task by ID."""
    session.execute(delete(RequestedTask).where(RequestedTask.id == requested_task_id))
