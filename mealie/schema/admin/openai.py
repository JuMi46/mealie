from datetime import datetime

from pydantic import UUID4, ConfigDict

from mealie.schema._mealie import MealieModel
from mealie.schema.response.pagination import PaginationBase


class OpenAIUsageLogOut(MealieModel):
    id: UUID4
    timestamp: datetime
    endpoint: str
    operation: str
    status: str

    model: str | None = None
    provider: str | None = None
    request_id: str | None = None

    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    latency_ms: int | None = None

    had_attachments: bool = False
    error_class: str | None = None
    error_message: str | None = None

    group_id: UUID4 | None = None
    household_id: UUID4 | None = None
    user_id: UUID4 | None = None
    user_name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class OpenAIUsageLogPagination(PaginationBase[OpenAIUsageLogOut]):
    items: list[OpenAIUsageLogOut]


class OpenAIUsageDailySummary(MealieModel):
    day: str
    requests: int
    input_tokens: int
    output_tokens: int
    total_tokens: int


class OpenAIUsageNamedSummary(MealieModel):
    name: str
    requests: int
    total_tokens: int


class OpenAIUsageSummaryOut(MealieModel):
    total_requests: int
    failed_requests: int
    input_tokens: int
    output_tokens: int
    total_tokens: int
    avg_latency_ms: int
    daily: list[OpenAIUsageDailySummary]
    top_endpoints: list[OpenAIUsageNamedSummary]
    top_models: list[OpenAIUsageNamedSummary]
