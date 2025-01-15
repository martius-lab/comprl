"""Leaderboard page."""

import reflex as rx

from ..components import standard_layout
from ..protected_state import UserDashboardState
from .. import reflex_local_auth


@rx.page(on_load=UserDashboardState.on_load)
@reflex_local_auth.require_login
def leaderboard() -> rx.Component:
    return standard_layout(
        rx.data_table(
            data=UserDashboardState.leaderboard_entries,
            columns=["Ranking", "Username", "µ / Σ"],
            search=True,
            sort=False,
            pagination=True,
            on_mount=UserDashboardState.update_ranked_users,
        ),
        heading="Leaderboard",
    )
