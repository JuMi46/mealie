from pydantic import UUID4
from sqlalchemy import and_, exists, not_, select

from mealie.db.models.household.shopping_list import ShoppingListItem
from mealie.db.models.recipe.api_extras import ShoppingListItemExtras
from mealie.schema.household.group_shopping_list import ShoppingListItemOut

from .repository_generic import HouseholdRepositoryGeneric


class RepositoryShoppingListItem(HouseholdRepositoryGeneric[ShoppingListItemOut, ShoppingListItem]):
    def get_next_unsent(self, shopping_list_id: UUID4 | None = None) -> ShoppingListItemOut | None:
        sent_exists = exists(
            select(1)
            .select_from(ShoppingListItemExtras)
            .where(
                and_(
                    ShoppingListItemExtras.shopping_list_item_id == ShoppingListItem.id,
                    ShoppingListItemExtras.key_name == "sent",
                    ShoppingListItemExtras.value == "true",
                )
            )
        )

        q = self._query().filter_by(**self._filter_builder(checked=False)).where(not_(sent_exists))

        if shopping_list_id:
            q = q.filter_by(**self._filter_builder(shopping_list_id=shopping_list_id))

        result = self.session.execute(q.order_by(ShoppingListItem.position.asc())).unique().scalars().first()

        if not result:
            return None

        return self.schema.model_validate(result)
