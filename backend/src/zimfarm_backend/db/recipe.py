from typing import Any
from uuid import UUID

from psycopg.errors import UniqueViolation
from sqlalchemy import Integer, func, select
from sqlalchemy import cast as sql_cast
from sqlalchemy.dialects.postgresql import JSONPATH, insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as OrmSession
from sqlalchemy.orm import selectinload

from zimfarm_backend import logger
from zimfarm_backend.common import constants, getnow
from zimfarm_backend.common.enums import (
    RecipeCategory,
    RecipePeriodicity,
    TaskStatus,
)
from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.common.schemas.models import (
    RecipeConfigSchema,
    RecipeNotificationSchema,
)
from zimfarm_backend.common.schemas.offliners.builder import generate_similarity_data
from zimfarm_backend.common.schemas.orms import (
    ConfigOfflinerOnlySchema,
    LanguageSchema,
    MostRecentTaskSchema,
    OfflinerDefinitionSchema,
    OfflinerSchema,
    RecipeDurationSchema,
    RecipeFullSchema,
    RecipeHistorySchema,
    RecipeLightSchema,
)
from zimfarm_backend.db import count_from_stmt
from zimfarm_backend.db.exceptions import (
    RecordAlreadyExistsError,
    RecordDoesNotExistError,
)
from zimfarm_backend.db.language import get_language_from_code
from zimfarm_backend.db.models import (
    OfflinerDefinition,
    Recipe,
    RecipeDuration,
    RecipeHistory,
    RequestedTask,
    Task,
    Worker,
)
from zimfarm_backend.db.offliner import get_offliner
from zimfarm_backend.db.offliner_definition import (
    create_offliner_instance,
    get_offliner_definition,
)
from zimfarm_backend.utils.timestamp import (
    get_status_timestamp_expr,
    get_timestamp_for_status,
)

DEFAULT_RECIPE_DURATION = RecipeDurationSchema(
    value=int(constants.DEFAULT_RECIPE_DURATION),
    on=getnow(),
    worker_name=None,
    default=True,
)


class RecipeListResult(BaseModel):
    nb_records: int
    recipes: list[RecipeLightSchema | RecipeFullSchema]


class RecipeHistoryListResult(BaseModel):
    nb_records: int
    history_entries: list[RecipeHistorySchema]


def count_enabled_recipes(session: OrmSession, recipe_names: list[str]) -> int:
    """Count all enabled recipes that match the given names"""
    return count_from_stmt(
        session,
        (
            select(Recipe).where(
                Recipe.enabled.is_(True),
                Recipe.archived.is_(False),
                Recipe.name.in_(recipe_names),
            )
        ),
    )


def get_recipe_or_none(session: OrmSession, *, recipe_name: str) -> Recipe | None:
    """Get a recipe for the given recipe name if possible else None"""
    return session.scalars(
        select(Recipe)
        .where(Recipe.name == recipe_name)
        .options(selectinload(Recipe.offliner_definition))
    ).one_or_none()


def get_recipe(session: OrmSession, *, recipe_name: str) -> Recipe:
    """Get a recipe for the given recipe name if possible else raise an exception"""
    if (recipe := get_recipe_or_none(session, recipe_name=recipe_name)) is None:
        raise RecordDoesNotExistError(f"Recipe with name {recipe_name} does not exist")
    return recipe


def map_duration(duration: RecipeDuration) -> RecipeDurationSchema:
    return RecipeDurationSchema(
        value=duration.value,
        on=duration.on,
        worker_name=duration.worker.name if duration.worker else None,
        default=duration.default,
    )


def _get_duration_for_recipe(recipe: Recipe, worker: Worker) -> RecipeDurationSchema:
    """get duration"""
    for duration in recipe.durations:
        if duration.worker and duration.worker.name == worker.name:
            return map_duration(duration)
    for duration in recipe.durations:
        if duration.default:
            return map_duration(duration)
    raise RecordDoesNotExistError(f"No default duration found for recipe {recipe.name}")


def get_recipe_duration(
    session: OrmSession, *, recipe_name: str | None, worker: Worker
) -> RecipeDurationSchema:
    """get duration for a recipe and worker (or default one)"""
    if recipe_name is None:
        return DEFAULT_RECIPE_DURATION
    recipe = get_recipe_or_none(session, recipe_name=recipe_name)
    if recipe is None:
        return DEFAULT_RECIPE_DURATION
    return _get_duration_for_recipe(recipe, worker)


def update_recipe_duration(
    session: OrmSession,
    *,
    recipe_name: str,
):
    """Update the duration for a recipe and worker"""
    recipe = get_recipe(session, recipe_name=recipe_name)
    # retrieve tasks that completed the resources intensive part
    # we don't mind to retrieve all of them because they are regularly purged
    tasks = session.execute(
        select(Task)
        .where(
            # Task timestamp has changed from dict[str, Any] to
            # list[tuple[str, Any]. As such we use jsonb_path query functions
            # to search for timestamp objects.
            func.jsonb_path_exists(
                Task.timestamp,
                sql_cast(f'$[*] ? (@[0] == "{TaskStatus.started}")', JSONPATH),
            ),
            func.jsonb_path_exists(
                Task.timestamp,
                sql_cast(
                    f'$[*] ? (@[0] == "{TaskStatus.scraper_completed}")', JSONPATH
                ),
            ),
            Task.container["exit_code"].astext.cast(Integer) == 0,
            Task.recipe_id == recipe.id,
        )
        .order_by(
            get_status_timestamp_expr(Task.timestamp, TaskStatus.scraper_completed),
        )
    ).scalars()

    workers_durations: dict[UUID, dict[str, Any]] = {}
    for task in tasks:
        workers_durations[task.worker_id] = {
            "value": int(
                (
                    get_timestamp_for_status(
                        task.timestamp, TaskStatus.scraper_completed
                    )
                    - get_timestamp_for_status(task.timestamp, TaskStatus.started)
                ).total_seconds()
            ),
            "on": get_timestamp_for_status(
                task.timestamp, TaskStatus.scraper_completed
            ),
        }

    # compute values that will be inserted (or updated) in the DB
    inserts_durations = [
        {
            "default": False,
            "value": duration_payload["value"],
            "on": duration_payload["on"],
            "recipe_id": recipe.id,
            "worker_id": worker_id,
        }
        for worker_id, duration_payload in workers_durations.items()
    ]

    # if there is no matching task for this recipe, just exit
    if len(inserts_durations) == 0:
        return

    # let's do an upsert ; conflict on recipe_id + worker_id
    # on conflict, set the on, value, task_id
    upsert_stmt = insert(RecipeDuration).values(inserts_durations)
    upsert_stmt = upsert_stmt.on_conflict_do_update(
        index_elements=[
            RecipeDuration.recipe_id,
            RecipeDuration.worker_id,
        ],
        set_={
            RecipeDuration.on: upsert_stmt.excluded.on,
            RecipeDuration.value: upsert_stmt.excluded.value,
        },
    )
    session.execute(upsert_stmt)


def get_recipes(
    session: OrmSession,
    *,
    skip: int,
    limit: int,
    name: str | None = None,
    lang: list[str] | None = None,
    categories: list[RecipeCategory] | None = None,
    tags: list[str] | None = None,
    archived: bool | None = None,
    omit_names: list[str] | None = None,
    similarity_data: list[str] | None = None,
    offliners: list[str] | None = None,
) -> RecipeListResult:
    """Get a list of recipes"""
    subquery = (
        select(
            func.count(RequestedTask.id).label("nb_requested_tasks"),
            RequestedTask.recipe_id,
        )
        .group_by(RequestedTask.recipe_id)
        .subquery("requested_task_count")
    )

    stmt = (
        select(
            func.count().over().label("total_records"),
            Recipe.name.label("recipe_name"),
            Recipe.category,
            Recipe.enabled,
            Recipe.language_code,
            OfflinerDefinition.offliner.label("offliner"),
            Task.id.label("task_id"),
            Task.status.label("task_status"),
            Task.updated_at.label("task_updated_at"),
            Task.timestamp,
            func.coalesce(subquery.c.nb_requested_tasks, 0).label("nb_requested_tasks"),
            Recipe.archived,
            Recipe.context,
        )
        .join(OfflinerDefinition, Recipe.offliner_definition)
        .join(Task, Recipe.most_recent_task, isouter=True)
        .join(subquery, subquery.c.recipe_id == Recipe.id, isouter=True)
        .order_by(Recipe.name)
        .where(
            # If a client provides an argument i.e it is not None,
            # we compare the corresponding model field against the argument,
            # otherwise, we compare the argument to its default which translates
            # to a SQL true i.e we don't filter based on this argument (a no-op).
            (Recipe.archived == archived) | (archived is None),
            (Recipe.category.in_(categories or []) | (categories is None)),
            (Recipe.language_code.in_(lang or []) | (lang is None)),
            (Recipe.tags.contains(tags or []) | (tags is None)),
            (
                Recipe.similarity_data.overlap(similarity_data or [])
                | (similarity_data is None)
            ),
            (
                Recipe.name.ilike(f"%{name if name is not None else ''}%")
                | (name is None)
            ),
            (Recipe.name.not_in(omit_names or []) | (omit_names is None)),
            (Recipe.config["offliner"]["offliner_id"].astext.in_(offliners or []))
            | (offliners is None),
        )
        .offset(skip)
        .limit(limit)
    )

    results = RecipeListResult(nb_records=0, recipes=[])

    for (
        nb_records,
        recipe_name,
        category,
        enabled,
        language_code,
        offliner,
        task_id,
        task_status,
        task_updated_at,
        task_timestamp,
        nb_requested_tasks,
        _archived,
        context,
    ) in session.execute(stmt).all():
        # Because the SQL window function returns the total_records
        # for every row, assign that value to the nb_records
        try:
            language = get_language_from_code(language_code)
        except RecordDoesNotExistError:
            language = LanguageSchema.model_validate(
                {"code": language_code, "name": language_code},
                context={"skip_validation": True},
            )

        results.nb_records = nb_records
        results.recipes.append(
            RecipeLightSchema(
                name=recipe_name,
                category=category,
                enabled=enabled,
                language=language,
                config=ConfigOfflinerOnlySchema(
                    offliner=offliner,
                ),
                most_recent_task=(
                    MostRecentTaskSchema(
                        id=task_id,
                        status=task_status,
                        updated_at=task_updated_at,
                        timestamp=task_timestamp,
                    )
                    if all([task_id, task_status, task_updated_at])
                    else None
                ),
                nb_requested_tasks=nb_requested_tasks,
                context=context,
                archived=_archived,
            )
        )

    return results


def _create_recipe_notification_schema(
    notification: dict[str, Any] | None,
) -> RecipeNotificationSchema:
    """Create recipe notification schema"""
    if notification:
        obj = RecipeNotificationSchema.model_validate(notification)
    else:
        obj = RecipeNotificationSchema()
    return obj


def create_recipe(
    session: OrmSession,
    *,
    author_id: UUID,
    name: str,
    category: RecipeCategory,
    language: LanguageSchema,
    config: RecipeConfigSchema,
    offliner_definition: OfflinerDefinitionSchema,
    tags: list[str],
    enabled: bool,
    notification: RecipeNotificationSchema | None,
    periodicity: RecipePeriodicity,
    context: str | None = None,
    comment: str | None = None,
) -> Recipe:
    """Create a new recipe"""
    offliner = get_offliner(session, offliner_definition.offliner)
    recipe = Recipe(
        name=name,
        category=category,
        language_code=language.code,
        config=config.model_dump(mode="json", context={"show_secrets": True}),
        tags=tags,
        enabled=enabled,
        notification=notification.model_dump(mode="json") if notification else None,
        periodicity=periodicity,
        context=context or "",
        similarity_data=generate_similarity_data(
            config.offliner.model_dump(mode="json", exclude={"offliner_id"}),
            offliner,
            offliner_definition.schema_,
        ),
    )
    recipe.offliner_definition_id = offliner_definition.id

    recipe_duration = RecipeDuration(
        value=DEFAULT_RECIPE_DURATION.value,
        on=DEFAULT_RECIPE_DURATION.on,
        default=True,
    )
    recipe.durations.append(recipe_duration)

    history_entry = RecipeHistory(
        created_at=getnow(),
        comment=comment,
        config=config.model_dump(mode="json"),
        name=recipe.name,
        category=recipe.category,
        enabled=recipe.enabled,
        language_code=recipe.language_code,
        tags=recipe.tags,
        periodicity=recipe.periodicity,
        context=recipe.context,
        offliner_definition_version=offliner_definition.version,
        notification=recipe.notification,
    )
    history_entry.author_id = author_id
    recipe.history_entries.append(history_entry)

    session.add(recipe)
    try:
        session.flush()
    except IntegrityError as exc:
        if isinstance(exc.orig, UniqueViolation):
            raise RecordAlreadyExistsError(
                f"Recipe with name {name} already exists"
            ) from exc
        logger.exception("Unknown exception encountered while creating recipe")
        raise

    session.refresh(recipe)

    return recipe


def create_recipe_full_schema(
    recipe: Recipe, offliner: OfflinerSchema, *, skip_validation: bool = True
) -> RecipeFullSchema:
    """Create a full recipe schema"""
    try:
        language = get_language_from_code(recipe.language_code)
    except RecordDoesNotExistError:
        language = LanguageSchema.model_validate(
            {"code": recipe.language_code, "name": recipe.language_code},
            context={"skip_validation": skip_validation},
        )
    return RecipeFullSchema(
        language=language,
        durations=[
            RecipeDurationSchema(
                value=duration.value,
                on=duration.on,
                worker_name=duration.worker.name if duration.worker else None,
                default=duration.default,
            )
            for duration in recipe.durations
        ],
        name=recipe.name,
        category=recipe.category,
        config=RecipeConfigSchema.model_validate(
            {
                **recipe.config,
                "offliner": create_offliner_instance(
                    offliner=offliner,
                    offliner_definition=recipe.offliner_definition,
                    data=recipe.config["offliner"],
                    skip_validation=skip_validation,
                ),
            },
            context={"skip_validation": skip_validation},
        ),
        enabled=recipe.enabled,
        tags=recipe.tags,
        periodicity=recipe.periodicity,
        similarity_data=recipe.similarity_data,
        notification=_create_recipe_notification_schema(recipe.notification),
        most_recent_task=(
            MostRecentTaskSchema(
                id=recipe.most_recent_task.id,
                status=recipe.most_recent_task.status,
                updated_at=recipe.most_recent_task.updated_at,
                timestamp=recipe.most_recent_task.timestamp,
            )
            if recipe.most_recent_task
            else None
        ),
        nb_requested_tasks=len(recipe.requested_tasks),
        is_valid=recipe.is_valid,
        context=recipe.context,
        offliner_definition_id=recipe.offliner_definition_id,
        version=recipe.offliner_definition.version,
        offliner=recipe.offliner_definition.offliner,
        archived=recipe.archived,
    )


def get_all_recipes(session: OrmSession, *, archived: bool = False) -> RecipeListResult:
    """Get all recipes"""
    result = RecipeListResult(nb_records=0, recipes=[])
    for recipe in session.scalars(
        select(Recipe).where(Recipe.archived == archived).order_by(Recipe.name)
    ).all():
        result.recipes.append(
            create_recipe_full_schema(
                recipe,
                get_offliner(session, recipe.config["offliner"]["offliner_id"]),
            )
        )
    result.nb_records = len(result.recipes)
    return result


def toggle_archive_status(
    session: OrmSession,
    *,
    actor_id: UUID,
    recipe_name: str,
    archived: bool,
    comment: str | None = None,
) -> Recipe:
    """Toggle the archive status of a recipe"""
    # Rather than using the update_recipe function, we use this one
    # because we don't want to create a history entry

    # Since we are toggling the archive status, the recipe in question must
    # be the opposite of the current archive status
    recipe = get_recipe(session, recipe_name=recipe_name)
    if recipe.archived == archived:
        raise RecordAlreadyExistsError(
            f"Recipe with name {recipe_name} already has archive status {archived}"
        )
    recipe.archived = archived
    history_entry = RecipeHistory(
        created_at=getnow(),
        comment=comment,
        config=recipe.config,
        name=recipe.name,
        category=recipe.category,
        enabled=recipe.enabled,
        language_code=recipe.language_code,
        tags=recipe.tags,
        periodicity=recipe.periodicity,
        context=recipe.context,
        archived=recipe.archived,
        offliner_definition_version=recipe.offliner_definition.version,
    )
    history_entry.author_id = actor_id
    recipe.history_entries.append(history_entry)
    session.add(recipe)
    session.flush()
    return recipe


def create_recipe_history_entry(
    session: OrmSession,
    *,
    recipe: Recipe,
    offliner_definition: OfflinerDefinitionSchema,
    comment: str | None,
    author_id: UUID,
) -> RecipeHistory:
    """Create a recipe history entry from a recipe."""
    history_entry = RecipeHistory(
        created_at=getnow(),
        comment=comment,
        config=recipe.config,
        name=recipe.name,
        category=recipe.category,
        enabled=recipe.enabled,
        language_code=recipe.language_code,
        tags=recipe.tags,
        periodicity=recipe.periodicity,
        context=recipe.context,
        archived=recipe.archived,
        offliner_definition_version=offliner_definition.version,
        notification=recipe.notification,
    )
    history_entry.author_id = author_id
    recipe.history_entries.append(history_entry)
    session.add(history_entry)

    return history_entry


def update_recipe(
    session: OrmSession,
    *,
    author_id: UUID,
    recipe_name: str,
    offliner_definition: OfflinerDefinitionSchema,
    new_recipe_config: RecipeConfigSchema | None = None,
    language: LanguageSchema | None = None,
    name: str | None = None,
    is_valid: bool | None = None,
    category: RecipeCategory | None = None,
    tags: list[str] | None = None,
    enabled: bool | None = None,
    periodicity: RecipePeriodicity | None = None,
    context: str | None = None,
    comment: str | None = None,
    notification: RecipeNotificationSchema | None = None,
) -> Recipe:
    """Update a recipe with the given values that are set."""
    recipe = get_recipe(session, recipe_name=recipe_name)

    if recipe.archived:
        raise RecordDoesNotExistError(f"Recipe with name {recipe_name} is archived")

    if new_recipe_config:
        recipe.config = new_recipe_config.model_dump(
            mode="json", context={"show_secrets": True}
        )
        recipe.similarity_data = generate_similarity_data(
            new_recipe_config.offliner.model_dump(mode="json", exclude={"offliner_id"}),
            get_offliner(session, offliner_definition.offliner),
            offliner_definition.schema_,
        )
    if language:
        recipe.language_code = language.code

    recipe.offliner_definition_id = offliner_definition.id
    recipe.name = name if name is not None else recipe.name
    recipe.category = category if category is not None else recipe.category
    recipe.tags = tags if tags is not None else recipe.tags
    recipe.enabled = enabled if enabled is not None else recipe.enabled
    recipe.periodicity = periodicity if periodicity is not None else recipe.periodicity
    recipe.is_valid = is_valid if is_valid is not None else recipe.is_valid
    recipe.notification = (
        notification.model_dump(mode="json") if notification else recipe.notification
    )

    recipe.context = context if context is not None else recipe.context
    session.add(recipe)
    create_recipe_history_entry(
        session,
        recipe=recipe,
        offliner_definition=offliner_definition,
        comment=comment,
        author_id=author_id,
    )
    try:
        session.flush()
    except IntegrityError as exc:
        if isinstance(exc.orig, UniqueViolation):
            raise RecordAlreadyExistsError(
                f"Recipe with name {name} already exists"
            ) from exc
        logger.exception("Unknown exception encountered while updating recipe")
        raise
    session.refresh(recipe)
    return recipe


def delete_recipe(session: OrmSession, *, recipe_name: str) -> None:
    """Delete a recipe"""
    recipe = get_recipe(session, recipe_name=recipe_name)
    # first unset most recent task to avoid circular dependency
    recipe.most_recent_task = None
    session.delete(recipe)
    session.flush()


def create_recipe_history_schema(
    history_entry: RecipeHistory,
) -> RecipeHistorySchema:
    return RecipeHistorySchema(
        id=history_entry.id,
        author=history_entry.author.display_name,
        created_at=history_entry.created_at,
        comment=history_entry.comment,
        name=history_entry.name,
        category=history_entry.category,
        enabled=history_entry.enabled,
        language_code=history_entry.language_code,
        tags=history_entry.tags,
        periodicity=history_entry.periodicity,
        context=history_entry.context,
        config=history_entry.config,
        archived=history_entry.archived,
        offliner_definition_version=history_entry.offliner_definition_version,
        notification=history_entry.notification,
    )


def get_recipe_history(
    session: OrmSession, *, recipe_id: UUID, skip: int, limit: int
) -> RecipeHistoryListResult:
    """Get a recipe's history"""
    stmt = (
        select(
            func.count().over().label("nb_records"),
            RecipeHistory,
        )
        .where(RecipeHistory.recipe_id == recipe_id)
        .order_by(RecipeHistory.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    results = RecipeHistoryListResult(nb_records=0, history_entries=[])
    for nb_records, history_entry in session.execute(stmt).all():
        results.nb_records = nb_records
        results.history_entries.append(create_recipe_history_schema(history_entry))
    return results


def get_recipe_history_entry_or_none(
    session: OrmSession, *, recipe_name: str, history_id: UUID
) -> RecipeHistory | None:
    """Get a recipe's history entry or None if it does not exist"""
    recipe = get_recipe(session, recipe_name=recipe_name)
    return session.scalars(
        select(RecipeHistory).where(
            RecipeHistory.id == history_id, RecipeHistory.recipe_id == recipe.id
        )
    ).one_or_none()


def get_recipe_history_entry(
    session: OrmSession, *, recipe_name: str, history_id: UUID
) -> RecipeHistory:
    """Get a recipe's history entry"""
    if history_entry := get_recipe_history_entry_or_none(
        session, recipe_name=recipe_name, history_id=history_id
    ):
        return history_entry
    raise RecordDoesNotExistError(
        f"Recipe '{recipe_name}' does not have a history entry with id {history_id}"
    )


def restore_recipes(
    session: OrmSession,
    *,
    actor_id: UUID,
    recipe_names: list[str],
    comment: str | None = None,
) -> None:
    """Restore a list of archived recipes"""
    for recipe_name in recipe_names:
        toggle_archive_status(
            session,
            actor_id=actor_id,
            recipe_name=recipe_name,
            archived=False,
            comment=comment,
        )


def revert_recipe(
    session: OrmSession,
    *,
    recipe_name: str,
    history_id: UUID,
    author_id: UUID,
    comment: str | None = None,
) -> Recipe:
    """Revert the recipe configuration and settings to those defined in history_id"""
    recipe = get_recipe(session, recipe_name=recipe_name)
    if recipe.archived:
        raise RecordDoesNotExistError(f"Recipe with name {recipe_name} is archived")

    history_entry = get_recipe_history_entry(
        session, recipe_name=recipe_name, history_id=history_id
    )
    if history_entry.offliner_definition_version is None:
        raise ValueError(
            "Cannot revert to history with no offliner definition version."
        )

    offliner = get_offliner(
        session, offliner_id=history_entry.config["offliner"]["offliner_id"]
    )
    offliner_definition = get_offliner_definition(
        session,
        offliner_id=offliner.id,
        version=history_entry.offliner_definition_version,
    )
    old_recipe_config = RecipeConfigSchema.model_validate(
        {
            **history_entry.config,
            "offliner": create_offliner_instance(
                offliner=offliner,
                offliner_definition=offliner_definition,
                data={**history_entry.config["offliner"]},
            ),
        }
    )
    # Copy over the attributes from the history entry to the recipe as both db
    # models are the same.
    recipe.config = old_recipe_config.model_dump(
        mode="json", context={"show_secrets": True}
    )
    recipe.similarity_data = generate_similarity_data(
        old_recipe_config.model_dump(mode="json", exclude={"offliner_id"}),
        offliner,
        offliner_definition.schema_,
    )
    recipe.language_code = history_entry.language_code
    recipe.offliner_definition_id = offliner_definition.id
    recipe.name = history_entry.name
    recipe.category = history_entry.category
    recipe.tags = history_entry.tags
    recipe.enabled = history_entry.enabled
    recipe.periodicity = history_entry.periodicity
    recipe.notification = history_entry.notification
    recipe.context = history_entry.context
    session.add(recipe)

    create_recipe_history_entry(
        session,
        recipe=recipe,
        offliner_definition=offliner_definition,
        author_id=author_id,
        comment=comment,
    )

    # Ensure that the recipe is valid
    create_recipe_full_schema(recipe, offliner, skip_validation=False)

    try:
        session.flush()
    except IntegrityError as exc:
        if isinstance(exc.orig, UniqueViolation):
            raise RecordAlreadyExistsError(
                f"Recipe with name {recipe.name} already exists"
            ) from exc
        logger.exception("Unknown exception encountered while updating recipe")
        raise
    session.refresh(recipe)

    return recipe
