from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from mealie.db.models.recipe.timer_active import RecipeTimerActive
from mealie.services.scheduler.tasks.delete_old_timers_active import delete_old_timers_active
from tests.utils.factories import random_string
from tests.utils.fixture_schemas import TestUser


def test_delete_old_timers_active(unique_user: TestUser):
    session = unique_user.repos.session
    now = datetime.now(UTC)

    old_timer = RecipeTimerActive(
        running=False,
        complete_time=now - timedelta(hours=13),
        text=random_string(),
        user_id=unique_user.user_id,
        group_id=unique_user.group_id,
        household_id=unique_user.household_id,
    )
    recent_timer = RecipeTimerActive(
        running=False,
        complete_time=now - timedelta(hours=11),
        text=random_string(),
        user_id=unique_user.user_id,
        group_id=unique_user.group_id,
        household_id=unique_user.household_id,
    )
    running_timer = RecipeTimerActive(
        running=True,
        complete_time=None,
        text=random_string(),
        user_id=unique_user.user_id,
        group_id=unique_user.group_id,
        household_id=unique_user.household_id,
    )

    session.add_all([old_timer, recent_timer, running_timer])
    session.commit()

    delete_old_timers_active()
    session.expire_all()

    remaining_ids = [timer.id for timer in session.scalars(select(RecipeTimerActive)).all()]

    assert old_timer.id not in remaining_ids
    assert recent_timer.id in remaining_ids
    assert running_timer.id in remaining_ids
