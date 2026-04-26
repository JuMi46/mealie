import datetime
import enum

from isodate import parse_time
from pydantic import UUID4, ConfigDict, model_validator

from mealie.schema._mealie import MealieModel
from mealie.schema._mealie.datetime_parse import parse_datetime
from mealie.schema.response.pagination import PaginationBase


class WebhookType(enum.StrEnum):
    mealplan = "mealplan"
    timer = "timer"


class TimerEvent(enum.StrEnum):
    started = "started"
    updated = "updated"
    stopped = "stopped"


class CreateWebhook(MealieModel):
    enabled: bool = True
    name: str = ""
    url: str = ""

    webhook_type: WebhookType = WebhookType.mealplan
    scheduled_time: datetime.time | None = None  # Only used for mealplan webhooks
    timer_event: TimerEvent | None = None  # Only used for timer webhooks
    is_deep_link: bool | None = None  # Only used for timer webhooks
    user_id: UUID4 | None = None  # Only used for timer webhooks

    @model_validator(mode="before")
    @classmethod
    def validate_scheduled_time(cls, values):
        """
        Validator accepts both datetime and time values from external sources.
        DateTime types are parsed and converted to time objects without timezones

        type: time is treated as a UTC value
        type: datetime is treated as a value with a timezone
        """
        if (
            isinstance(values, dict)
            and values.get("webhook_type") == WebhookType.mealplan
            and values.get("scheduled_time") is None
        ):
            values["scheduled_time"] = lambda: datetime.datetime.now(datetime.UTC).time()

        if (
            isinstance(values, dict)
            and values.get("webhook_type") == WebhookType.mealplan
            and values.get("scheduled_time") is not None
        ):
            v = values["scheduled_time"]
            parser_funcs = [
                lambda x: parse_datetime(x).astimezone(datetime.UTC).time(),
                parse_time,
            ]

            if isinstance(v, datetime.time):
                return values  # No change needed

            for parser_func in parser_funcs:
                try:
                    values["scheduled_time"] = parser_func(v)
                    return values
                except ValueError:
                    continue

            raise ValueError(f"Invalid scheduled time: {v}")

        if isinstance(values, dict) and values.get("webhook_type") == WebhookType.timer:
            if values.get("timer_event") is None:
                values["timer_event"] = TimerEvent.started
            if values.get("is_deep_link") is None:
                values["is_deep_link"] = False

        return values


class SaveWebhook(CreateWebhook):
    group_id: UUID4
    household_id: UUID4


class ReadWebhook(SaveWebhook):
    id: UUID4
    model_config = ConfigDict(from_attributes=True)


class TimerWebhookTestIn(MealieModel):
    timer_id: str = ""
    length: str = "300"
    message: str = "Test Webhook"
    recipe_link: str = ""
    complete_time: str = ""
    complete_time_in_ms: int | None = None


class WebhookPagination(PaginationBase):
    items: list[ReadWebhook]
