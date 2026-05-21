from datetime import UTC, datetime, timedelta
from math import ceil

from fastapi import APIRouter, Depends
from pydantic import UUID4
from sqlalchemy import String, case, cast, delete, func, or_, select

from mealie.db.models.group import OpenAIUsageLogModel
from mealie.db.models.users import User
from mealie.routes._base import BaseAdminController, controller
from mealie.schema.admin.openai import (
    OpenAIUsageDailySummary,
    OpenAIUsageLogOut,
    OpenAIUsageLogPagination,
    OpenAIUsageNamedSummary,
    OpenAIUsageSummaryOut,
)
from mealie.schema.response.pagination import PaginationQuery
from mealie.schema.response.responses import SuccessResponse

router = APIRouter(prefix="/openai")


@controller(router)
class AdminOpenAIController(BaseAdminController):
    def _filtered_query(
        self,
        *,
        all_groups: bool,
        group_id: UUID4 | None,
        user_id: UUID4 | None,
        user_name: str | None,
        endpoint: str | None,
        status: str | None,
        model: str | None,
        search: str | None,
        start_at: datetime | None,
        end_at: datetime | None,
    ):
        query = select(OpenAIUsageLogModel, User.username.label("user_name")).outerjoin(
            User, OpenAIUsageLogModel.user_id == User.id
        )

        if all_groups:
            if group_id:
                query = query.where(OpenAIUsageLogModel.group_id == group_id)
        else:
            query = query.where(OpenAIUsageLogModel.group_id == self.user.group_id)

        if user_id:
            query = query.where(OpenAIUsageLogModel.user_id == user_id)
        if user_name:
            query = query.where(func.lower(User.username).contains(user_name.lower()))
        if endpoint:
            query = query.where(func.lower(OpenAIUsageLogModel.endpoint).contains(endpoint.lower()))
        if status:
            query = query.where(func.lower(OpenAIUsageLogModel.status).contains(status.lower()))
        if model:
            query = query.where(func.lower(OpenAIUsageLogModel.model).contains(model.lower()))
        if start_at:
            query = query.where(OpenAIUsageLogModel.timestamp >= start_at)
        if end_at:
            query = query.where(OpenAIUsageLogModel.timestamp <= end_at)

        if search:
            search_lc = search.lower()
            query = query.where(
                or_(
                    func.lower(OpenAIUsageLogModel.endpoint).contains(search_lc),
                    func.lower(OpenAIUsageLogModel.status).contains(search_lc),
                    func.lower(func.coalesce(User.username, "")).contains(search_lc),
                    cast(OpenAIUsageLogModel.timestamp, String).contains(search),
                )
            )

        return query

    @router.get("/logs", response_model=OpenAIUsageLogPagination)
    def get_logs(
        self,
        q: PaginationQuery = Depends(PaginationQuery),
        all_groups: bool = False,
        group_id: UUID4 | None = None,
        user_id: UUID4 | None = None,
        user_name: str | None = None,
        endpoint: str | None = None,
        status: str | None = None,
        model: str | None = None,
        search: str | None = None,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
    ):
        base_query = self._filtered_query(
            all_groups=all_groups,
            group_id=group_id,
            user_id=user_id,
            user_name=user_name,
            endpoint=endpoint,
            status=status,
            model=model,
            search=search,
            start_at=start_at,
            end_at=end_at,
        )

        count_stmt = select(func.count()).select_from(base_query.subquery())
        total = int(self.session.execute(count_stmt).scalar() or 0)

        per_page = q.per_page if q.per_page > 0 else max(total, 1)
        page = max(q.page, 1)
        offset = (page - 1) * per_page

        items_stmt = (
            base_query.order_by(OpenAIUsageLogModel.timestamp.desc(), OpenAIUsageLogModel.created_at.desc())
            .offset(offset)
            .limit(per_page)
        )
        rows = self.session.execute(items_stmt).all()

        response = OpenAIUsageLogPagination(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=max(ceil(total / per_page), 1),
            items=[
                OpenAIUsageLogOut.model_validate(
                    {
                        **OpenAIUsageLogOut.model_validate(row[0]).model_dump(),
                        "user_name": row.user_name,
                    }
                )
                for row in rows
            ],
        )
        response.set_pagination_guides(
            router.url_path_for("get_logs"),
            {
                **q.model_dump(exclude_none=True),
                "all_groups": all_groups,
                "group_id": group_id,
                "user_id": user_id,
                "user_name": user_name,
                "endpoint": endpoint,
                "status": status,
                "model": model,
                "search": search,
                "start_at": start_at,
                "end_at": end_at,
            },
        )
        return response

    @router.get("/summary", response_model=OpenAIUsageSummaryOut)
    def get_summary(
        self,
        all_groups: bool = False,
        group_id: UUID4 | None = None,
        user_id: UUID4 | None = None,
        user_name: str | None = None,
        endpoint: str | None = None,
        status: str | None = None,
        model: str | None = None,
        search: str | None = None,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
    ):
        base_query = self._filtered_query(
            all_groups=all_groups,
            group_id=group_id,
            user_id=user_id,
            user_name=user_name,
            endpoint=endpoint,
            status=status,
            model=model,
            search=search,
            start_at=start_at,
            end_at=end_at,
        )
        q_sub = base_query.subquery()

        agg_stmt = select(
            func.count().label("total_requests"),
            func.sum(case((q_sub.c.status != "success", 1), else_=0)).label("failed_requests"),
            func.coalesce(func.sum(q_sub.c.input_tokens), 0).label("input_tokens"),
            func.coalesce(func.sum(q_sub.c.output_tokens), 0).label("output_tokens"),
            func.coalesce(func.sum(q_sub.c.total_tokens), 0).label("total_tokens"),
            func.coalesce(func.avg(q_sub.c.latency_ms), 0).label("avg_latency_ms"),
        )
        agg = self.session.execute(agg_stmt).first()

        daily_stmt = (
            select(
                func.date(q_sub.c.timestamp).label("day"),
                func.count().label("requests"),
                func.coalesce(func.sum(q_sub.c.input_tokens), 0).label("input_tokens"),
                func.coalesce(func.sum(q_sub.c.output_tokens), 0).label("output_tokens"),
                func.coalesce(func.sum(q_sub.c.total_tokens), 0).label("total_tokens"),
            )
            .group_by(func.date(q_sub.c.timestamp))
            .order_by(func.date(q_sub.c.timestamp).desc())
            .limit(30)
        )
        endpoint_stmt = (
            select(
                q_sub.c.endpoint.label("name"),
                func.count().label("requests"),
                func.coalesce(func.sum(q_sub.c.total_tokens), 0).label("total_tokens"),
            )
            .group_by(q_sub.c.endpoint)
            .order_by(func.count().desc())
            .limit(10)
        )
        model_stmt = (
            select(
                q_sub.c.model.label("name"),
                func.count().label("requests"),
                func.coalesce(func.sum(q_sub.c.total_tokens), 0).label("total_tokens"),
            )
            .group_by(q_sub.c.model)
            .order_by(func.count().desc())
            .limit(10)
        )

        daily_rows = self.session.execute(daily_stmt).all()
        endpoint_rows = self.session.execute(endpoint_stmt).all()
        model_rows = self.session.execute(model_stmt).all()

        return OpenAIUsageSummaryOut(
            total_requests=int(getattr(agg, "total_requests", 0) or 0),
            failed_requests=int(getattr(agg, "failed_requests", 0) or 0),
            input_tokens=int(getattr(agg, "input_tokens", 0) or 0),
            output_tokens=int(getattr(agg, "output_tokens", 0) or 0),
            total_tokens=int(getattr(agg, "total_tokens", 0) or 0),
            avg_latency_ms=int(getattr(agg, "avg_latency_ms", 0) or 0),
            daily=[
                OpenAIUsageDailySummary(
                    day=str(row.day),
                    requests=int(row.requests or 0),
                    input_tokens=int(row.input_tokens or 0),
                    output_tokens=int(row.output_tokens or 0),
                    total_tokens=int(row.total_tokens or 0),
                )
                for row in daily_rows
                if row.day
            ],
            top_endpoints=[
                OpenAIUsageNamedSummary(
                    name=row.name or "unknown",
                    requests=int(row.requests or 0),
                    total_tokens=int(row.total_tokens or 0),
                )
                for row in endpoint_rows
            ],
            top_models=[
                OpenAIUsageNamedSummary(
                    name=row.name or "unknown",
                    requests=int(row.requests or 0),
                    total_tokens=int(row.total_tokens or 0),
                )
                for row in model_rows
            ],
        )

    @router.post("/prune", response_model=SuccessResponse)
    def prune_logs(self, days: int = 90):
        cutoff = datetime.now(UTC) - timedelta(days=max(days, 1))

        stmt = delete(OpenAIUsageLogModel).where(OpenAIUsageLogModel.timestamp < cutoff)
        deleted = self.session.execute(stmt).rowcount or 0
        self.session.commit()

        return SuccessResponse.respond(f"Deleted {deleted} OpenAI usage log entries older than {days} days")
