from typing import TYPE_CHECKING

import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Mapped, mapped_column

from mealie.db.models._model_base import BaseMixins, SqlAlchemyBase
from mealie.db.models._model_utils.auto_init import auto_init
from mealie.db.models._model_utils.guid import GUID

if TYPE_CHECKING:
    from ..labels import MultiPurposeLabel
    from ..recipe import IngredientFoodModel
    from .household import Household


class HouseholdIngredientFoodLabel(SqlAlchemyBase, BaseMixins):
    __tablename__ = "households_to_ingredient_food_labels"
    __table_args__ = (sa.UniqueConstraint("household_id", "food_id", name="household_id_food_id_label_key"),)

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=GUID.generate)
    household_id: Mapped[GUID] = mapped_column(GUID, sa.ForeignKey("households.id"), nullable=False, index=True)
    food_id: Mapped[GUID] = mapped_column(GUID, sa.ForeignKey("ingredient_foods.id"), nullable=False, index=True)
    label_id: Mapped[GUID] = mapped_column(GUID, sa.ForeignKey("multi_purpose_labels.id"), nullable=False, index=True)

    household: Mapped["Household"] = orm.relationship("Household", back_populates="ingredient_food_label_overrides")
    food: Mapped["IngredientFoodModel"] = orm.relationship("IngredientFoodModel", back_populates="household_label_overrides")
    label: Mapped["MultiPurposeLabel"] = orm.relationship("MultiPurposeLabel")

    @auto_init()
    def __init__(self, **_) -> None:
        pass
