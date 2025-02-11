"""User dashboard page."""

import reflex as rx

from ..components import standard_layout
from ..protected_state import UserDashboardState
from .. import reflex_local_auth
from ..reflex_local_auth.local_auth import LocalAuthState


@rx.page(on_load=UserDashboardState.on_load)
@reflex_local_auth.require_login
def dashboard() -> rx.Component:
    win_rate = round(
        UserDashboardState.game_statistics.num_games_won
        / UserDashboardState.game_statistics.num_games_played
        * 100
    )

    return standard_layout(
        rx.hstack(
            rx.card(
                rx.heading("User Information", style={"margin-bottom": "1rem"}),
                rx.data_list.root(
                    rx.data_list.item(
                        rx.data_list.label("username"),
                        rx.data_list.value(LocalAuthState.authenticated_user.username),
                    ),
                    rx.data_list.item(
                        rx.data_list.label("Access Token"),
                        rx.data_list.value(LocalAuthState.authenticated_user.token),
                    ),
                    rx.data_list.item(
                        rx.data_list.label("Ranking"),
                        rx.data_list.value(
                            f"{UserDashboardState.ranking_position}. place"
                        ),
                    ),
                    rx.data_list.item(
                        rx.data_list.label("Games Played"),
                        rx.data_list.value(
                            UserDashboardState.game_statistics.num_games_played
                        ),
                    ),
                    rx.data_list.item(
                        rx.data_list.label("Games Won"),
                        rx.data_list.value(
                            UserDashboardState.game_statistics.num_games_won
                        ),
                    ),
                    rx.data_list.item(
                        rx.data_list.label("Win rate"),
                        rx.data_list.value(f"{win_rate} %"),
                    ),
                    rx.data_list.item(
                        rx.data_list.label("Disconnects"),
                        rx.data_list.value(
                            UserDashboardState.game_statistics.num_disconnects
                        ),
                    ),
                ),
            ),
            rx.card(
                rx.heading("Client Configuration", style={"margin-bottom": "1rem"}),
                rx.spacer(),
                rx.code_block(UserDashboardState.client_config, language="bash"),
                rx.text("The client code can be found here: "),
                rx.link(
                    "GitHub: martius-lab/comprl-hockey-agent",
                    href="https://github.com/martius-lab/comprl-hockey-agent",
                ),
            ),
        ),
        heading="Dashboard",
    )
