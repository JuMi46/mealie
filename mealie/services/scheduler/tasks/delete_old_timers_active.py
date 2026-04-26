import datetime

from sqlalchemy import delete

from mealie.core import root_logger
from mealie.db.db_setup import session_context
from mealie.db.models.recipe.timer_active import RecipeTimerActiveModel

logger = root_logger.get_logger()

MAX_HOURS_OLD = 3


def delete_old_timers_active() -> None:
    """Deletes recipe active timers with a complete_time older than 3 hours."""
    logger.debug("purging recipe active timers older than %d hours", MAX_HOURS_OLD)
    limit = datetime.datetime.now(datetime.UTC) - datetime.timedelta(hours=MAX_HOURS_OLD)

    with session_context() as session:
        stmt = delete(RecipeTimerActiveModel).filter(RecipeTimerActiveModel.complete_time <= limit)
        session.execute(stmt)
        session.commit()
        session.close()
        logger.info("recipe active timers older than %d hours purged", MAX_HOURS_OLD)
