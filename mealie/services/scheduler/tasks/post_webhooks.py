from datetime import UTC, datetime
from urllib.parse import quote

import requests
from pydantic import UUID4
from sqlalchemy import or_, select

from mealie.db.db_setup import session_context
from mealie.db.models.household.webhooks import GroupWebhooksModel
from mealie.repos.all_repositories import get_repositories
from mealie.schema.household.webhook import ReadWebhook, TimerEvent
from mealie.schema.response.pagination import PaginationQuery
from mealie.services.event_bus_service.event_bus_listeners import WebhookEventListener
from mealie.services.event_bus_service.event_bus_service import EventBusService
from mealie.services.event_bus_service.event_types import (
    INTERNAL_INTEGRATION_ID,
    Event,
    EventBusMessage,
    EventDocumentType,
    EventOperation,
    EventTypes,
    EventWebhookData,
)

last_ran = datetime.now(UTC)


def post_group_webhooks(
    start_dt: datetime | None = None, group_id: UUID4 | None = None, household_id: UUID4 | None = None
) -> None:
    """Post webhook events to specified group, or all groups"""

    global last_ran

    # if not specified, start the query at the last time the service ran
    start_dt = start_dt or last_ran

    # end the query at the current time
    last_ran = end_dt = datetime.now(UTC)

    if group_id is None:
        # publish the webhook event to each group's event bus

        with session_context() as session:
            repos = get_repositories(session)
            groups_data = repos.groups.page_all(PaginationQuery(page=1, per_page=-1))
            group_ids = [group.id for group in groups_data.items]

    else:
        group_ids = [group_id]

    """
    At this time only mealplan webhooks are supported. To add support for more types,
    add a dispatch event for that type here (e.g. EventDocumentType.recipe_bulk_report) and
    handle the webhook data in the webhook event bus listener
    """

    event_type = EventTypes.webhook_task
    event_document_data = EventWebhookData(
        document_type=EventDocumentType.mealplan,
        operation=EventOperation.info,
        webhook_start_dt=start_dt,
        webhook_end_dt=end_dt,
    )

    for group_id in group_ids:
        if household_id is None:
            with session_context() as session:
                household_repos = get_repositories(session, group_id=group_id)
                households_data = household_repos.households.page_all(PaginationQuery(page=1, per_page=-1))
                household_ids = [household.id for household in households_data.items]
        else:
            household_ids = [household_id]

        for household_id in household_ids:
            event_bus = EventBusService()
            event_bus.dispatch(
                integration_id=INTERNAL_INTEGRATION_ID,
                group_id=group_id,
                household_id=household_id,
                event_type=event_type,
                document_data=event_document_data,
            )


def post_test_webhook(webhook: ReadWebhook, message: str = "") -> None:
    dt = datetime.min.replace(tzinfo=UTC)
    event_type = EventTypes.test_message

    event_document_data = EventWebhookData(
        document_type=EventDocumentType.generic,
        operation=EventOperation.info,
        webhook_start_dt=dt,
        webhook_end_dt=dt,
    )
    event = Event(
        message=EventBusMessage.from_type(event_type, body=message),
        event_type=event_type,
        integration_id=INTERNAL_INTEGRATION_ID,
        document_data=event_document_data,
    )

    listener = WebhookEventListener(webhook.group_id, webhook.household_id)
    listener.publish_to_subscribers(event, [webhook])


def post_test_timer_webhook(
    webhook: ReadWebhook,
    timer_id: str = "",
    length: str = "300",
    message: str = "Test Webhook",
    recipe_link: str = "",
    complete_time: str = "",
    complete_time_in_ms: int | None = None,
) -> None:
    timer_event = webhook.timer_event or TimerEvent.started
    effective_complete_time, effective_complete_time_in_ms = _resolve_complete_time_values(
        complete_time,
        complete_time_in_ms,
    )
    _send_timer_webhook(
        webhook,
        timer_id=timer_id,
        timer_event=timer_event,
        length=length,
        message=message,
        recipe_link=recipe_link,
        complete_time=effective_complete_time,
        complete_time_in_ms=effective_complete_time_in_ms,
    )


def post_timer_webhooks_on_event(
    *,
    group_id: UUID4,
    household_id: UUID4,
    user_id: UUID4,
    timer_id: str,
    timer_event: TimerEvent,
    length: str,
    message: str,
    recipe_link: str,
    complete_time: str,
    complete_time_in_ms: int,
) -> None:
    with session_context() as session:
        stmt = select(GroupWebhooksModel).where(
            GroupWebhooksModel.enabled == True,  # noqa: E712 - required for SQLAlchemy comparison
            GroupWebhooksModel.group_id == group_id,
            GroupWebhooksModel.household_id == household_id,
            GroupWebhooksModel.webhook_type == "timer",
            GroupWebhooksModel.timer_event == timer_event.value,
            or_(GroupWebhooksModel.user_id.is_(None), GroupWebhooksModel.user_id == user_id),
        )

        webhooks = session.execute(stmt).scalars().all()

    for webhook in webhooks:
        _send_timer_webhook(
            webhook,
            timer_id=timer_id,
            timer_event=timer_event,
            length=length,
            message=message,
            recipe_link=recipe_link,
            complete_time=complete_time,
            complete_time_in_ms=complete_time_in_ms,
        )


def _send_timer_webhook(
    webhook: ReadWebhook,
    *,
    timer_id: str,
    timer_event: TimerEvent,
    length: str,
    message: str,
    recipe_link: str,
    complete_time: str,
    complete_time_in_ms: int,
) -> None:
    show_length = timer_event in (TimerEvent.started, TimerEvent.updated)
    safe_length = quote(length if show_length else "", safe="")
    safe_message = quote(message, safe="")

    parsed_url = (webhook.url or "").replace("{length}", safe_length).replace("{message}", safe_message)

    if webhook.is_deep_link:
        requests.post(parsed_url, timeout=15)
        return

    payload: dict[str, str | int] = {
        "action": _timer_action_for_event(timer_event),
        "timerId": timer_id,
        "length": length if show_length else "",
        "message": message,
        "recipeLink": recipe_link,
        "completeTime": complete_time,
        "completeTimeInMs": complete_time_in_ms,
    }

    requests.post(parsed_url, json=payload, timeout=15)


def _timer_action_for_event(timer_event: TimerEvent) -> str:
    if timer_event == TimerEvent.started:
        return "create"
    if timer_event == TimerEvent.updated:
        return "update"
    return "delete"


def _resolve_complete_time_values(complete_time: str, complete_time_in_ms: int | None) -> tuple[str, int]:
    if complete_time_in_ms is not None and complete_time:
        return complete_time, complete_time_in_ms

    if complete_time_in_ms is not None:
        resolved_dt = datetime.fromtimestamp(complete_time_in_ms / 1000, tz=UTC)
        return resolved_dt.isoformat(), complete_time_in_ms

    if complete_time:
        parsed = _parse_complete_time(complete_time)
        if parsed is not None:
            return complete_time, int(parsed.timestamp() * 1000)

    fallback = datetime.now(UTC)
    return fallback.isoformat(), int(fallback.timestamp() * 1000)


def _parse_complete_time(value: str) -> datetime | None:
    try:
        normalized = value.replace("Z", "+00:00") if value.endswith("Z") else value
        parsed = datetime.fromisoformat(normalized)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
    except ValueError:
        return None
