from datetime import UTC, datetime
from functools import cached_property

from fastapi import BackgroundTasks
from pydantic import UUID4

from mealie.routes._base.base_controllers import BaseUserController
from mealie.routes._base.controller import controller
from mealie.routes._base.mixins import HttpRepo
from mealie.routes._base.routers import MealieCrudRoute, UserAPIRouter
from mealie.schema import mapper
from mealie.schema.household.webhook import TimerEvent
from mealie.schema.recipe.recipe_timer_active import (
    RecipeTimerActive,
    RecipeTimerActiveCreate,
    RecipeTimerActiveDelete,
    RecipeTimerActiveSave,
    RecipeTimerActiveUpdate,
)
from mealie.services.scheduler.tasks.post_webhooks import post_timer_webhooks_on_event

router = UserAPIRouter(prefix="/timers", route_class=MealieCrudRoute, tags=["Recipe: Timers active"])


@controller(router)
class RecipeTimersActiveRoutes(BaseUserController):
    @cached_property
    def repo(self):
        return self.repos.recipe_timers_active

    # =======================================================================
    # CRUD Operations

    @property
    def mixins(self) -> HttpRepo:
        return HttpRepo(self.repo, self.logger, self.registered_exceptions, self.t("generic.server-error"))

    @router.post(
        "/{recipe_timer_id}/active",
        response_model=RecipeTimerActive,
    )
    def create_active_timer(self, recipe_timer_id: UUID4, data: RecipeTimerActiveCreate, bg_tasks: BackgroundTasks):
        """Create an active timer for a recipe instruction"""
        user_id = self.user.id

        save = mapper.cast(
            data,
            RecipeTimerActiveSave,
            recipe_timer_id=recipe_timer_id,
            user_id=user_id,
            group_id=self.group_id,
            household_id=self.household_id,
        )
        created = self.mixins.create_one(save)
        if created is None:
            raise ValueError("Failed to create active timer")

        bg_tasks.add_task(
            post_timer_webhooks_on_event,
            group_id=self.group_id,
            household_id=self.household_id,
            user_id=user_id,
            timer_event=TimerEvent.started,
            length=_timer_length_from_complete_time(created.complete_time),
            message=created.text or "",
            recipe_link=data.recipe_link or "",
            complete_time=created.complete_time.isoformat(),
            complete_time_in_ms=int(created.complete_time.timestamp() * 1000),
        )
        return created

    @router.post(
        "/recipes/{recipe_id}/active",
        response_model=RecipeTimerActive,
    )
    def create_active_timer_on_recipe(self, recipe_id: UUID4, data: RecipeTimerActiveCreate, bg_tasks: BackgroundTasks):
        """Create an active timer for a recipe"""
        user_id = self.user.id

        save = mapper.cast(
            data,
            RecipeTimerActiveSave,
            recipe_id=recipe_id,
            user_id=user_id,
            group_id=self.group_id,
            household_id=self.household_id,
        )
        created = self.mixins.create_one(save)
        if created is None:
            raise ValueError("Failed to create active timer")

        bg_tasks.add_task(
            post_timer_webhooks_on_event,
            group_id=self.group_id,
            household_id=self.household_id,
            user_id=user_id,
            timer_event=TimerEvent.started,
            length=_timer_length_from_complete_time(created.complete_time),
            message=created.text or "",
            recipe_link=data.recipe_link or "",
            complete_time=created.complete_time.isoformat(),
            complete_time_in_ms=int(created.complete_time.timestamp() * 1000),
        )
        return created

    @router.put(
        "/active/{timer_active_id}",
        response_model=RecipeTimerActive,
    )
    def update_timer_active(self, timer_active_id: UUID4, data: RecipeTimerActiveUpdate):
        """Update an active timer, for example when complete_time changes"""
        return self.mixins.patch_one(data, timer_active_id)

    @router.get(
        "/active/{timer_active_id}",
        response_model=RecipeTimerActive,
    )
    def get_active_timer(self, timer_active_id: UUID4):
        """Get one active timer by id"""
        return self.mixins.get_one(timer_active_id)

    @router.delete(
        "/active/{timer_active_id}",
        response_model=RecipeTimerActive,
    )
    def delete_active_timer(
        self, timer_active_id: UUID4, bg_tasks: BackgroundTasks, data: RecipeTimerActiveDelete | None = None
    ):
        """Delete one active timer by id"""
        user_id = self.user.id

        active_timer = self.mixins.get_one(timer_active_id)
        deleted = self.mixins.delete_one(timer_active_id)

        if active_timer:
            bg_tasks.add_task(
                post_timer_webhooks_on_event,
                group_id=self.group_id,
                household_id=self.household_id,
                user_id=user_id,
                timer_event=TimerEvent.stopped,
                length="",
                message=active_timer.text or "",
                recipe_link=(data.recipe_link if data else "") or "",
                complete_time=active_timer.complete_time.isoformat(),
                complete_time_in_ms=int(active_timer.complete_time.timestamp() * 1000),
            )

        return deleted

    @router.get(
        "/active",
        response_model=list[RecipeTimerActive],
    )
    def get_active_timers(self):
        """List active timers for the current household"""
        return self.repo.get_all(order_by="created_at", override=RecipeTimerActive)


def _timer_length_from_complete_time(complete_time: datetime) -> str:
    complete = complete_time if complete_time.tzinfo else complete_time.replace(tzinfo=UTC)
    delta_seconds = int(max(0, (complete - datetime.now(UTC)).total_seconds()))
    return str(delta_seconds)
