from pydantic import ConfigDict
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .._model_base import BaseMixins, SqlAlchemyBase
from .._model_utils.auto_init import auto_init
from .._model_utils.guid import GUID


class RecipeInstructionTimer(SqlAlchemyBase, BaseMixins):
    __tablename__ = "recipe_instruction_timers"
    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=GUID.generate)
    duration: Mapped[int] = mapped_column(Integer)
    text: Mapped[str | None] = mapped_column(String)
    recipe_instruction_id: Mapped[GUID | None] = mapped_column(GUID, ForeignKey("recipe_instructions.id"), index=True)

    model_config = ConfigDict(from_attributes=True)

    @auto_init()
    def __init__(self, **_) -> None:
        pass
