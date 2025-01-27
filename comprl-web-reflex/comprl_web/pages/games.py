"""Game overview.

List of all games of the logged in user.
"""

import reflex as rx

from ..components import standard_layout
from ..protected_state import UserGamesState, GameInfo
from .. import reflex_local_auth


def show_game(game: GameInfo) -> rx.Component:
    """Show a game in a table row."""
    return rx.table.row(
        rx.table.cell(game.player1),
        rx.table.cell(game.player2),
        rx.table.cell(game.result),
        rx.table.cell(game.time),
        rx.table.cell(game.id),
        rx.table.cell(
            rx.cond(
                game.has_game_file,
                rx.button(
                    "Download game data",
                    on_click=lambda: UserGamesState.download_game(game.id),
                ),
                rx.text("No game data", align="center", style={"font-style": "italic"}),
            )
        ),
    )


def user_game_table() -> rx.Component:
    """Render the user game table."""
    return rx.vstack(
        rx.form(
            rx.hstack(
                rx.text("Search for game ID:"),
                rx.input(
                    name="search_id",
                    placeholder="Game ID",
                    width="38ex",
                ),
                rx.button("Search"),
            ),
            on_submit=UserGamesState.search_game,
        ),
        rx.cond(
            UserGamesState.search_id,
            rx.hstack(
                rx.text(f"Search results for game ID: {UserGamesState.search_id}"),
                rx.button("Clear search", on_click=UserGamesState.clear_search),
            ),
        ),
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.foreach(
                        UserGamesState.user_games_header, rx.table.column_header_cell
                    )
                ),
            ),
            rx.table.body(rx.foreach(UserGamesState.user_games, show_game)),
            on_mount=UserGamesState.load_user_games,
            width="100%",
        ),
        rx.hstack(
            rx.button(
                "First",
                on_click=UserGamesState.first_page,
            ),
            rx.button(
                "Prev",
                on_click=UserGamesState.prev_page,
            ),
            rx.text(
                f"Page {UserGamesState.page_number} / {UserGamesState.total_pages}"
            ),
            rx.button(
                "Next",
                on_click=UserGamesState.next_page,
            ),
        ),
    )


@rx.page(on_load=UserGamesState.on_load)
@reflex_local_auth.require_login
def game_overview() -> rx.Component:
    return standard_layout(
        user_game_table(),
        heading="Games",
    )
