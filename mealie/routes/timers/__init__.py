from datetime import UTC, datetime
from functools import cached_property

import jwt
from fastapi import APIRouter, BackgroundTasks, Query, WebSocket, WebSocketDisconnect
from jwt.exceptions import PyJWTError
from pydantic import UUID4
from sqlalchemy.orm.session import Session

from mealie.core.config import get_app_settings
from mealie.core.dependencies.dependencies import ALGORITHM, TokenData, validate_long_live_token
from mealie.db.db_setup import session_context
from mealie.repos.all_repositories import get_repositories
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
from mealie.schema.user import PrivateUser
from mealie.services.scheduler.tasks.post_webhooks import post_timer_webhooks_on_event

router = UserAPIRouter(prefix="/timers", route_class=MealieCrudRoute, tags=["Recipe: Timers active"])
ws_router = APIRouter(prefix="/timers", tags=["Recipe: Timers active WebSocket"])

_settings = get_app_settings()


class TimerActiveWebsocketManager:
    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = {}

    async def connect(self, household_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.setdefault(household_id, set()).add(websocket)

    def disconnect(self, household_id: str, websocket: WebSocket) -> None:
        household_sockets = self._connections.get(household_id)
        if household_sockets:
            household_sockets.discard(websocket)
            if not household_sockets:
                del self._connections[household_id]

    async def broadcast(self, household_id: str, payload: dict) -> None:
        household_sockets = self._connections.get(household_id)
        if not household_sockets:
            return
        dead: list[WebSocket] = []
        for ws in list(household_sockets):
            try:
                await ws.send_json(payload)
            except (RuntimeError, WebSocketDisconnect):
                dead.append(ws)
        for ws in dead:
            self.disconnect(household_id, ws)


timer_active_websocket_manager = TimerActiveWebsocketManager()


async def _authenticate_websocket_user(
    websocket: WebSocket,
    session: Session,
    token: str | None,
) -> PrivateUser | None:
    # Try query-param token first, then cookie
    raw_token = token or websocket.cookies.get("mealie.access_token", "")
    if not raw_token:
        return None
    try:
        payload = jwt.decode(raw_token, _settings.SECRET, algorithms=[ALGORITHM])
        long_token: str | None = payload.get("long_token")
        if long_token is not None:
            return validate_long_live_token(session, raw_token, payload.get("id"))
        user_id: str | None = payload.get("sub")
        if user_id is None:
            return None
        token_data = TokenData(user_id=user_id)
    except PyJWTError:
        return None
    repos = get_repositories(session, group_id=None, household_id=None)
    return repos.users.get_one(token_data.user_id, "id", any_case=False)


def _timer_active_event_payload(event: str, active_timer: RecipeTimerActive) -> dict:
    return {
        "type": "timer-active",
        "event": event,
        "timerActive": active_timer.model_dump(mode="json", by_alias=True),
    }


@ws_router.websocket("/ws/active")
async def timer_active_websocket(
    websocket: WebSocket,
    token: str | None = Query(default=None),
):
    with session_context() as session:
        user = await _authenticate_websocket_user(websocket, session, token)
    if user is None:
        await websocket.close(code=4001)
        return

    household_id = str(user.household_id)
    await timer_active_websocket_manager.connect(household_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        timer_active_websocket_manager.disconnect(household_id, websocket)


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
            timer_id=str(created.id),
            timer_event=TimerEvent.started,
            length=_timer_length_from_complete_time(created.complete_time),
            message=created.text or "",
            recipe_link=data.recipe_link or "",
            complete_time=created.complete_time.isoformat(),
            complete_time_in_ms=int(created.complete_time.timestamp() * 1000),
        )
        bg_tasks.add_task(
            timer_active_websocket_manager.broadcast,
            str(self.household_id),
            _timer_active_event_payload("created", created),
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
            timer_id=str(created.id),
            timer_event=TimerEvent.started,
            length=_timer_length_from_complete_time(created.complete_time),
            message=created.text or "",
            recipe_link=data.recipe_link or "",
            complete_time=created.complete_time.isoformat(),
            complete_time_in_ms=int(created.complete_time.timestamp() * 1000),
        )
        bg_tasks.add_task(
            timer_active_websocket_manager.broadcast,
            str(self.household_id),
            _timer_active_event_payload("created", created),
        )
        return created

    @router.put(
        "/active/{timer_active_id}",
        response_model=RecipeTimerActive,
    )
    def update_timer_active(self, timer_active_id: UUID4, data: RecipeTimerActiveUpdate, bg_tasks: BackgroundTasks):
        """Update an active timer, for example when complete_time changes"""
        user_id = self.user.id
        updated = self.mixins.patch_one(data, timer_active_id)
        if updated is None:
            return updated

        bg_tasks.add_task(
            post_timer_webhooks_on_event,
            group_id=self.group_id,
            household_id=self.household_id,
            user_id=user_id,
            timer_id=str(updated.id),
            timer_event=TimerEvent.updated,
            length=_timer_length_from_complete_time(updated.complete_time),
            message=updated.text or "",
            recipe_link="",
            complete_time=updated.complete_time.isoformat(),
            complete_time_in_ms=int(updated.complete_time.timestamp() * 1000),
        )
        bg_tasks.add_task(
            timer_active_websocket_manager.broadcast,
            str(self.household_id),
            _timer_active_event_payload("updated", updated),
        )
        return updated

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
                timer_id=str(active_timer.id),
                timer_event=TimerEvent.stopped,
                length="",
                message=active_timer.text or "",
                recipe_link=(data.recipe_link if data else "") or "",
                complete_time=active_timer.complete_time.isoformat(),
                complete_time_in_ms=int(active_timer.complete_time.timestamp() * 1000),
            )
            bg_tasks.add_task(
                timer_active_websocket_manager.broadcast,
                str(self.household_id),
                _timer_active_event_payload("deleted", active_timer),
            )
        return deleted

    @router.post(
        "/active/{timer_active_id}/webhook/stopped",
        response_model=RecipeTimerActive,
    )
    def post_stopped_webhook_for_active_timer(
        self, timer_active_id: UUID4, bg_tasks: BackgroundTasks, data: RecipeTimerActiveDelete | None = None
    ):
        """Trigger stopped timer webhooks for an active timer without deleting it"""
        user_id = self.user.id
        active_timer = self.mixins.get_one(timer_active_id)

        if active_timer:
            bg_tasks.add_task(
                post_timer_webhooks_on_event,
                group_id=self.group_id,
                household_id=self.household_id,
                user_id=user_id,
                timer_id=str(active_timer.id),
                timer_event=TimerEvent.stopped,
                length="",
                message=active_timer.text or "",
                recipe_link=(data.recipe_link if data else "") or "",
                complete_time=active_timer.complete_time.isoformat(),
                complete_time_in_ms=int(active_timer.complete_time.timestamp() * 1000),
            )

        return active_timer

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
