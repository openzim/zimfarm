from collections.abc import Sequence
from typing import Any, cast
from uuid import UUID

from psycopg.errors import UniqueViolation
from pydantic import Field
from sqlalchemy import Integer, exists, func, select, update
from sqlalchemy import cast as sql_cast
from sqlalchemy.dialects.postgresql import JSONPATH, insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as OrmSession
from sqlalchemy.orm import selectinload

from zimfarm_backend import logger
from zimfarm_backend.common import constants, getnow, is_valid_uuid
from zimfarm_backend.common.enums import (
    RecipePeriodicity,
    TaskStatus,
)
from zimfarm_backend.common.schemas import BaseModel
from zimfarm_backend.common.schemas.fields import NotEmptyString
from zimfarm_backend.common.schemas.models import (
    RecipeConfigSchema,
    RecipeNotificationSchema,
)
from zimfarm_backend.common.schemas.offliners.builder import generate_similarity_data
from zimfarm_backend.common.schemas.orms import (
    ConfigOfflinerOnlySchema,
    LanguageSchema,
    ListResult,
    MostRecentTaskSchema,
    OfflinerDefinitionSchema,
    OfflinerSchema,
    RecipeDurationSchema,
    RecipeFullSchema,
    RecipeHistorySchema,
    RecipeLightSchema,
    TeamLightSchema,
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
    Team,
    TeamRecipe,
)
from zimfarm_backend.db.offliner import get_offliner
from zimfarm_backend.db.offliner_definition import (
    create_offliner_definition_schema,
    create_offliner_instance,
    get_offliner_definition,
)
from zimfarm_backend.db.team import get_team_by_name
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


class RecipeCreateSchema(BaseModel):
    name: str
    language: LanguageSchema
    config: RecipeConfigSchema
    tags: list[str]
    enabled: bool
    notification: RecipeNotificationSchema | None
    periodicity: RecipePeriodicity
    context: str | None = None
    comment: str | None = None
    teams: list[str] = Field(min_length=1)


class RecipeUpdateSchema(BaseModel):
    offliner_definition: OfflinerDefinitionSchema
    config: RecipeConfigSchema | None = None
    language: LanguageSchema | None = None
    name: NotEmptyString | None = None
    is_valid: bool | None = None
    tags: list[NotEmptyString] | None = None
    teams: list[NotEmptyString] | None = Field(default=None, min_length=1)
    enabled: bool | None = None
    periodicity: RecipePeriodicity | None = None
    context: str | None = None
    comment: str | None = None
    notification: RecipeNotificationSchema | None = None


def count_enabled_recipes(
    session: OrmSession,
    recipe_names: list[str],
    accessible_team_ids: None | Sequence[UUID],
) -> int:
    """Count all enabled recipes that match the given names"""
    return count_from_stmt(
        session,
        (
            select(Recipe).where(
                Recipe.enabled.is_(True),
                Recipe.archived.is_(False),
                Recipe.name.in_(recipe_names),
                exists().where(
                    TeamRecipe.recipe_id == Recipe.id,
                    TeamRecipe.team_id.in_(accessible_team_ids or []),
                )
                | (accessible_team_ids is None),
            )
        ),
    )


def get_recipe_or_none(
    session: OrmSession,
    recipe_identifier: str,
    accessible_team_ids: None | Sequence[UUID],
) -> Recipe | None:
    """Get a recipe by id or name if accessible else None"""
    if is_valid_uuid(recipe_identifier):
        where_clause = Recipe.id == recipe_identifier
    else:
        where_clause = Recipe.name == recipe_identifier
    return session.scalars(
        select(Recipe)
        .where(
            where_clause,
            exists().where(
                TeamRecipe.recipe_id == Recipe.id,
                TeamRecipe.team_id.in_(accessible_team_ids or []),
            )
            | (accessible_team_ids is None),
        )
        .options(selectinload(Recipe.offliner_definition))
    ).one_or_none()


def get_recipe(
    session: OrmSession,
    recipe_identifier: str,
    accessible_team_ids: None | Sequence[UUID],
) -> Recipe:
    """Get a recipe for the given recipe name if possible else raise an exception"""
    if (
        recipe := get_recipe_or_none(session, recipe_identifier, accessible_team_ids)
    ) is None:
        raise RecordDoesNotExistError(
            f"Recipe {recipe_identifier} does not exist or is not accessible to you."
        )
    return recipe


def map_duration(duration: RecipeDuration) -> RecipeDurationSchema:
    return RecipeDurationSchema(
        value=duration.value,
        on=duration.on,
        worker_name=duration.worker.name if duration.worker else None,
        default=duration.default,
    )


def get_duration_for_recipe(recipe: Recipe, worker_name: str) -> RecipeDurationSchema:
    """get duration"""
    for duration in recipe.durations:
        if duration.worker and duration.worker.name == worker_name:
            return map_duration(duration)
    for duration in recipe.durations:
        if duration.default:
            return map_duration(duration)
    raise RecordDoesNotExistError(f"No default duration found for recipe {recipe.name}")


def get_recipe_duration(
    session: OrmSession,
    *,
    recipe_identifier: str | None,
    worker_name: str,
    accessible_team_ids: None | Sequence[UUID],
) -> RecipeDurationSchema:
    """get duration for a recipe and worker (or default one)"""
    if recipe_identifier is None:
        return DEFAULT_RECIPE_DURATION
    recipe = get_recipe_or_none(
        session, recipe_identifier, accessible_team_ids=accessible_team_ids
    )
    if recipe is None:
        return DEFAULT_RECIPE_DURATION
    return get_duration_for_recipe(recipe, worker_name)


def update_recipe_duration(
    session: OrmSession,
    *,
    recipe_identifier: str,
    accessible_team_ids: None | Sequence[UUID],
):
    """Update the duration for a recipe and worker"""
    recipe = get_recipe(
        session, recipe_identifier, accessible_team_ids=accessible_team_ids
    )
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
    accessible_team_ids: Sequence[UUID] | None,
    name: str | None = None,
    lang: list[str] | None = None,
    tags: list[str] | None = None,
    archived: bool | None = None,
    omit_names: list[str] | None = None,
    similarity_data: list[str] | None = None,
    offliners: list[str] | None = None,
    teams: list[str] | None = None,
) -> ListResult[RecipeLightSchema]:
    """Get a list of recipes"""
    subquery = (
        select(
            func.count(RequestedTask.id).label("nb_requested_tasks"),
            RequestedTask.recipe_id,
        )
        .group_by(RequestedTask.recipe_id)
        .subquery("requested_task_count")
    )

    teams_subquery = (
        select(
            func.jsonb_agg(
                func.jsonb_build_object(
                    "name",
                    Team.name,
                    "is_private",
                    Team.is_private,
                )
            )
        )
        .select_from(TeamRecipe)
        .join(Team, Team.id == TeamRecipe.team_id)
        .where(TeamRecipe.recipe_id == Recipe.id)
        .correlate(Recipe)
        .scalar_subquery()
        .label("teams")
    )

    stmt = (
        select(
            Recipe.id.label("recipe_id"),
            Recipe.name.label("recipe_name"),
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
            teams_subquery,
        )
        .distinct()
        .join(TeamRecipe, TeamRecipe.recipe_id == Recipe.id)
        .join(Team, Team.id == TeamRecipe.team_id)
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
            (Team.name.in_(teams or []) | (teams is None)),
            TeamRecipe.team_id.in_(accessible_team_ids or [])
            | (accessible_team_ids is None),
        )
    )

    return ListResult[RecipeLightSchema](
        nb_records=count_from_stmt(session, stmt),
        records=[
            RecipeLightSchema(
                id=recipe_id,
                name=recipe_name,
                enabled=enabled,
                language=get_language_from_code(
                    language_code,
                    fallback=LanguageSchema.model_validate(
                        {"code": language_code, "name": language_code},
                        context={"skip_validation": True},
                    ),
                ),
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
                teams=sorted(
                    [
                        TeamLightSchema.model_validate(team)
                        for team in cast("list[dict[str, Any]]", teams_json or [])
                    ],
                    key=lambda team: team.name,
                ),
            )
            for (
                recipe_id,
                recipe_name,
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
                teams_json,
            ) in session.execute(stmt.offset(skip).limit(limit)).all()
        ],
    )


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
    payload: RecipeCreateSchema,
    offliner_definition: OfflinerDefinitionSchema,
    accessible_team_ids: Sequence[UUID] | None,
) -> Recipe:
    """Create a new recipe"""
    offliner = get_offliner(session, offliner_definition.offliner)
    recipe = Recipe(
        name=payload.name,
        language_code=payload.language.code,
        config=payload.config.model_dump(mode="json", context={"show_secrets": True}),
        tags=payload.tags,
        enabled=payload.enabled,
        notification=payload.notification.model_dump(mode="json")
        if payload.notification
        else None,
        periodicity=payload.periodicity,
        context=payload.context or "",
        similarity_data=generate_similarity_data(
            payload.config.offliner.model_dump(mode="json", exclude={"offliner_id"}),
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

    for team_name in payload.teams:
        team = get_team_by_name(
            session, team_name, accessible_team_ids=accessible_team_ids
        )
        team_recipe = TeamRecipe()
        team_recipe.team = team
        team_recipe.recipe = recipe
        session.add(team_recipe)

    create_recipe_history_entry(
        session,
        recipe=recipe,
        offliner_definition=offliner_definition,
        comment=payload.comment,
        author_id=author_id,
    )

    session.add(recipe)
    try:
        session.flush()
    except IntegrityError as exc:
        if isinstance(exc.orig, UniqueViolation):
            raise RecordAlreadyExistsError(
                f"Recipe with name {payload.name} already exists"
            ) from exc
        logger.exception("Unknown exception encountered while creating recipe")
        raise

    session.refresh(recipe)

    return recipe


def create_recipe_full_schema(
    recipe: Recipe, offliner: OfflinerSchema, *, skip_validation: bool = True
) -> RecipeFullSchema:
    """Create a full recipe schema"""
    language = get_language_from_code(
        recipe.language_code,
        fallback=LanguageSchema.model_validate(
            {"code": recipe.language_code, "name": recipe.language_code},
            context={"skip_validation": skip_validation},
        ),
    )
    return RecipeFullSchema(
        id=recipe.id,
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
        teams=[
            TeamLightSchema(name=entry.team.name, is_private=entry.team.is_private)
            for entry in recipe.teams
        ],
    )


def get_all_recipes(
    session: OrmSession,
    *,
    accessible_team_ids: Sequence[UUID] | None,
    archived: bool = False,
) -> ListResult[RecipeFullSchema]:
    """Get all recipes"""
    result = ListResult[RecipeFullSchema](nb_records=0, records=[])
    for recipe in session.scalars(
        select(Recipe)
        .join(TeamRecipe, TeamRecipe.recipe_id == Recipe.id)
        .where(
            Recipe.archived == archived,
            TeamRecipe.team_id.in_(accessible_team_ids or [])
            | (accessible_team_ids is None),
        )
        .order_by(Recipe.name)
    ).all():
        result.records.append(
            create_recipe_full_schema(
                recipe,
                get_offliner(session, recipe.config["offliner"]["offliner_id"]),
            )
        )
    result.nb_records = len(result.records)
    return result


def toggle_archive_status(
    session: OrmSession,
    *,
    actor_id: UUID,
    recipe_identifier: str,
    archived: bool,
    accessible_team_ids: Sequence[UUID] | None,
    comment: str | None = None,
) -> Recipe:
    """Toggle the archive status of a recipe"""
    # Rather than using the update_recipe function, we use this one
    # because we don't want to create a history entry

    # Since we are toggling the archive status, the recipe in question must
    # be the opposite of the current archive status
    recipe = get_recipe(session, recipe_identifier, accessible_team_ids)
    if recipe.archived == archived:
        raise RecordAlreadyExistsError(
            f"Recipe  {recipe_identifier} already has archive status {archived}"
        )
    recipe.archived = archived
    create_recipe_history_entry(
        session,
        recipe=recipe,
        offliner_definition=create_offliner_definition_schema(
            recipe.offliner_definition
        ),
        comment=comment,
        author_id=actor_id,
    )
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
        enabled=recipe.enabled,
        language_code=recipe.language_code,
        tags=recipe.tags,
        periodicity=recipe.periodicity,
        context=recipe.context,
        archived=recipe.archived,
        offliner_definition_version=offliner_definition.version,
        notification=recipe.notification,
        teams=[
            {
                "name": rt.team.name,
                "is_private": rt.team.is_private,
            }
            for rt in recipe.teams
        ],
    )
    history_entry.author_id = author_id
    recipe.history_entries.append(history_entry)
    session.add(history_entry)

    return history_entry


def update_recipe(
    session: OrmSession,
    *,
    author_id: UUID,
    recipe_identifier: str,
    accessible_team_ids: Sequence[UUID] | None,
    payload: RecipeUpdateSchema,
) -> Recipe:
    """Update a recipe with the given values that are set."""
    recipe = get_recipe(session, recipe_identifier, accessible_team_ids)

    if recipe.archived:
        raise RecordDoesNotExistError(f"Recipe  {recipe_identifier} is archived")

    update_data = {
        key: value
        for key, value in payload.model_dump(
            exclude_unset=True,
            mode="json",
            exclude={
                "offliner_definition",
                "config",
                "language",
                "comment",
                "teams",
            },
        ).items()
        if value is not None
    }

    if payload.config:
        update_data["config"] = payload.config.model_dump(
            mode="json", context={"show_secrets": True}
        )
        update_data["similarity_data"] = generate_similarity_data(
            payload.config.offliner.model_dump(mode="json", exclude={"offliner_id"}),
            get_offliner(session, payload.offliner_definition.offliner),
            payload.offliner_definition.schema_,
        )
    if payload.language:
        update_data["language_code"] = payload.language.code

    # Return early if no update data
    updated = False
    if update_data:
        update_data["offliner_definition_id"] = payload.offliner_definition.id
        try:
            recipe = session.scalars(
                update(Recipe)
                .where(Recipe.id == recipe.id)
                .values(**update_data)
                .returning(Recipe)
            ).one()
        except IntegrityError as exc:
            raise RecordAlreadyExistsError(
                f"Recipe with name '{payload.name}' already exists"
            ) from exc
        updated = True

    if payload.teams is not None:
        current_team_names = {team_recipe.team.name for team_recipe in recipe.teams}
        new_team_names = set(payload.teams)

        for team_recipe in list(recipe.teams):
            if team_recipe.team.name not in new_team_names:
                recipe.teams.remove(team_recipe)
                session.delete(team_recipe)

        for team_name in new_team_names - current_team_names:
            team = get_team_by_name(
                session, team_name, accessible_team_ids=accessible_team_ids
            )
            team_recipe = TeamRecipe()
            team_recipe.team = team
            team_recipe.recipe = recipe
            session.add(team_recipe)
        updated = True

    if not updated:
        return recipe

    create_recipe_history_entry(
        session,
        recipe=recipe,
        offliner_definition=payload.offliner_definition,
        comment=payload.comment,
        author_id=author_id,
    )
    session.flush()
    session.refresh(recipe)
    return recipe


def delete_recipe(
    session: OrmSession,
    recipe_identifier: str,
    accessible_team_ids: Sequence[UUID] | None,
) -> None:
    """Delete a recipe"""
    recipe = get_recipe(session, recipe_identifier, accessible_team_ids)
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
        enabled=history_entry.enabled,
        language_code=history_entry.language_code,
        tags=history_entry.tags,
        periodicity=history_entry.periodicity,
        context=history_entry.context,
        config=history_entry.config,
        archived=history_entry.archived,
        offliner_definition_version=history_entry.offliner_definition_version,
        notification=history_entry.notification,
        teams=[
            TeamLightSchema(name=entry["name"], is_private=bool(entry["is_private"]))
            for entry in history_entry.teams
        ],
    )


def get_recipe_history(
    session: OrmSession,
    *,
    recipe_identifier: str,
    accessible_team_ids: Sequence[UUID] | None,
    skip: int,
    limit: int,
) -> ListResult[RecipeHistorySchema]:
    """Get a recipe's history"""
    recipe = get_recipe(
        session, recipe_identifier, accessible_team_ids=accessible_team_ids
    )
    stmt = (
        select(
            func.count().over().label("nb_records"),
            RecipeHistory,
        )
        .where(RecipeHistory.recipe_id == recipe.id)
        .order_by(RecipeHistory.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    results = ListResult[RecipeHistorySchema](nb_records=0, records=[])
    for nb_records, history_entry in session.execute(stmt).all():
        results.nb_records = nb_records
        results.records.append(create_recipe_history_schema(history_entry))
    return results


def get_recipe_history_entry_or_none(
    session: OrmSession,
    *,
    recipe_identifier: str,
    history_id: UUID,
    accessible_team_ids: Sequence[UUID] | None,
) -> RecipeHistory | None:
    """Get a recipe's history entry or None if it does not exist"""
    recipe = get_recipe(session, recipe_identifier, accessible_team_ids)
    return session.scalars(
        select(RecipeHistory).where(
            RecipeHistory.id == history_id, RecipeHistory.recipe_id == recipe.id
        )
    ).one_or_none()


def get_recipe_history_entry(
    session: OrmSession,
    *,
    recipe_identifier: str,
    history_id: UUID,
    accessible_team_ids: Sequence[UUID] | None,
) -> RecipeHistory:
    """Get a recipe's history entry"""
    if history_entry := get_recipe_history_entry_or_none(
        session,
        recipe_identifier=recipe_identifier,
        history_id=history_id,
        accessible_team_ids=accessible_team_ids,
    ):
        return history_entry
    raise RecordDoesNotExistError(
        f"Recipe '{recipe_identifier}' does not have a history entry with id "
        f"{history_id}"
    )


def restore_recipes(
    session: OrmSession,
    *,
    actor_id: UUID,
    recipe_identifiers: list[str],
    accessible_team_ids: Sequence[UUID] | None,
    comment: str | None = None,
) -> None:
    """Restore a list of archived recipes"""
    for recipe_identifier in recipe_identifiers:
        toggle_archive_status(
            session,
            actor_id=actor_id,
            recipe_identifier=recipe_identifier,
            archived=False,
            accessible_team_ids=accessible_team_ids,
            comment=comment,
        )


def revert_recipe(
    session: OrmSession,
    *,
    recipe_identifier: str,
    history_id: UUID,
    author_id: UUID,
    accessible_team_ids: Sequence[UUID] | None,
    comment: str | None = None,
) -> Recipe:
    """Revert the recipe configuration and settings to those defined in history_id"""
    history_entry = get_recipe_history_entry(
        session,
        recipe_identifier=recipe_identifier,
        history_id=history_id,
        accessible_team_ids=accessible_team_ids,
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
    language = get_language_from_code(
        history_entry.language_code,
        fallback=LanguageSchema.model_validate(
            {"code": history_entry.language_code, "name": history_entry.language_code},
            context={"skip_validation": True},
        ),
    )
    team_names = [team["name"] for team in history_entry.teams]

    recipe = update_recipe(
        session,
        author_id=author_id,
        recipe_identifier=recipe_identifier,
        accessible_team_ids=accessible_team_ids,
        payload=RecipeUpdateSchema(
            offliner_definition=offliner_definition,
            config=old_recipe_config,
            language=language,
            name=history_entry.name,
            is_valid=True,
            tags=history_entry.tags,
            teams=team_names or None,
            enabled=history_entry.enabled,
            periodicity=RecipePeriodicity(history_entry.periodicity),
            context=history_entry.context,
            comment=comment,
            notification=_create_recipe_notification_schema(history_entry.notification),
        ),
    )

    # Ensure that the recipe is valid
    create_recipe_full_schema(recipe, offliner, skip_validation=False)
    return recipe
