from functools import cached_property

from pydantic import UUID4

from mealie.routes._base.base_controllers import BaseUserController
from mealie.routes._base.controller import controller
from mealie.routes._base.mixins import HttpRepo
from mealie.routes._base.routers import MealieCrudRoute, UserAPIRouter
from mealie.schema import mapper
from mealie.schema.recipe.recipe_timer_active import (
    RecipeTimerActive,
    RecipeTimerActiveCreate,
    RecipeTimerActiveSave,
    RecipeTimerActiveUpdate,
)

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
    def create_active_timer(self, recipe_timer_id: UUID4, data: RecipeTimerActiveCreate):
        """Create an active timer for a recipe instruction"""
        save = mapper.cast(
            data,
            RecipeTimerActiveSave,
            recipe_timer_id=recipe_timer_id,
            user_id=self.user.id,
            group_id=self.group_id,
            household_id=self.household_id,
        )
        return self.mixins.create_one(save)

    @router.post(
        "/recipes/{recipe_id}/active",
        response_model=RecipeTimerActive,
    )
    def create_active_timer_on_recipe(self, recipe_id: UUID4, data: RecipeTimerActiveCreate):
        """Create an active timer for a recipe"""
        save = mapper.cast(
            data,
            RecipeTimerActiveSave,
            recipe_id=recipe_id,
            user_id=self.user.id,
            group_id=self.group_id,
            household_id=self.household_id,
        )
        return self.mixins.create_one(save)

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
    def delete_active_timer(self, timer_active_id: UUID4):
        """Delete one active timer by id"""
        return self.mixins.delete_one(timer_active_id)

    @router.get(
        "/active",
        response_model=list[RecipeTimerActive],
    )
    def get_active_timers(self):
        """List active timers for the current household"""
        return self.repo.get_all(order_by="created_at", override=RecipeTimerActive)
