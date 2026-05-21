from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, orm
from sqlalchemy.orm import Mapped, mapped_column

from mealie.db.models._model_base import BaseMixins, SqlAlchemyBase
from mealie.db.models._model_utils.auto_init import auto_init
from mealie.db.models._model_utils.datetime import NaiveDateTime, get_utc_now
from mealie.db.models._model_utils.guid import GUID

if TYPE_CHECKING:
    from mealie.db.models.group.group import Group


class OpenAIUsageLogModel(SqlAlchemyBase, BaseMixins):
    __tablename__ = "openai_usage_logs"

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=GUID.generate)
    timestamp: Mapped[datetime] = mapped_column(NaiveDateTime, nullable=False, default=get_utc_now, index=True)
    endpoint: Mapped[str] = mapped_column(String, nullable=False, index=True)
    operation: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, index=True)

    model: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    provider: Mapped[str | None] = mapped_column(String, nullable=True)
    request_id: Mapped[str | None] = mapped_column(String, nullable=True)

    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    had_attachments: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    error_class: Mapped[str | None] = mapped_column(String, nullable=True)
    error_message: Mapped[str | None] = mapped_column(String, nullable=True)

    group_id: Mapped[GUID | None] = mapped_column(GUID, ForeignKey("groups.id"), nullable=True, index=True)
    household_id: Mapped[GUID | None] = mapped_column(GUID, ForeignKey("households.id"), nullable=True, index=True)
    user_id: Mapped[GUID | None] = mapped_column(GUID, ForeignKey("users.id"), nullable=True, index=True)

    group: Mapped["Group"] = orm.relationship("Group", back_populates="openai_usage_logs")

    @auto_init()
    def __init__(self, **_) -> None:
        pass
