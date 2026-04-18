import datetime

from pydantic import ConfigDict
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from .._model_base import BaseMixins, SqlAlchemyBase
from .._model_utils.auto_init import auto_init
from .._model_utils.datetime import NaiveDateTime
from .._model_utils.guid import GUID


class RecipeTimerActiveModel(SqlAlchemyBase, BaseMixins):
    __tablename__ = "recipe_timers_active"
    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=GUID.generate)
    complete_time: Mapped[datetime.datetime] = mapped_column(NaiveDateTime)
    text: Mapped[str | None] = mapped_column(String)

    recipe_id: Mapped[GUID | None] = mapped_column(GUID, ForeignKey("recipes.id"), index=True)
    recipe_timer_id: Mapped[GUID | None] = mapped_column(
        GUID, ForeignKey("recipe_timers.id"), index=True
    )  # Should either be linked to a instruction timer or to a custom recipe timer, but not both
    household_id: Mapped[GUID | None] = mapped_column(GUID, ForeignKey("households.id"), index=True)
    group_id: Mapped[GUID | None] = mapped_column(GUID, ForeignKey("groups.id"), index=True)
    user_id: Mapped[GUID | None] = mapped_column(GUID, ForeignKey("users.id"), index=True)

    model_config = ConfigDict(from_attributes=True)

    @auto_init()
    def __init__(self, **_) -> None:
        pass
