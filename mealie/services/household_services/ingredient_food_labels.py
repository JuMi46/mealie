from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import sqlalchemy as sa
from pydantic import UUID4
from sqlalchemy.orm import Session, joinedload

from mealie.db.models.household.ingredient_food_label import HouseholdIngredientFoodLabel
from mealie.schema.labels.multi_purpose_label import MultiPurposeLabelSummary


def get_household_food_label_map(
    session: Session,
    household_id: UUID4 | None,
    food_ids: Iterable[Any],
) -> dict[UUID4, MultiPurposeLabelSummary]:
    if household_id is None:
        return {}

    valid_food_ids = {food_id for food_id in food_ids if food_id is not None}
    if not valid_food_ids:
        return {}

    stmt = (
        sa.select(HouseholdIngredientFoodLabel)
        .options(joinedload(HouseholdIngredientFoodLabel.label))
        .where(
            HouseholdIngredientFoodLabel.household_id == household_id,
            HouseholdIngredientFoodLabel.food_id.in_(valid_food_ids),
        )
    )
    rows = session.execute(stmt).unique().scalars().all()

    return {row.food_id: MultiPurposeLabelSummary.model_validate(row.label) for row in rows if row.label is not None}
