from pydantic import ConfigDict
from sqlalchemy import ForeignKey, Integer, String, orm
from sqlalchemy.orm import Mapped, mapped_column

from mealie.db.models.recipe.timer_active import RecipeTimerActiveModel

from .._model_base import BaseMixins, SqlAlchemyBase
from .._model_utils.auto_init import auto_init
from .._model_utils.guid import GUID


class RecipeTimerModel(SqlAlchemyBase, BaseMixins):
    __tablename__ = "recipe_timers"
    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=GUID.generate)
    duration: Mapped[int] = mapped_column(Integer)
    text: Mapped[str | None] = mapped_column(String)
    recipe_instruction_id: Mapped[GUID | None] = mapped_column(GUID, ForeignKey("recipe_instructions.id"), index=True)
    timers_active: Mapped[list["RecipeTimerActiveModel"]] = orm.relationship(
        "RecipeTimerActiveModel", cascade="all, delete-orphan", single_parent=True
    )
    model_config = ConfigDict(from_attributes=True)

    @auto_init()
    def __init__(self, **_) -> None:
        pass
