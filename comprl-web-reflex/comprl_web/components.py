"""Components used on multiple pages."""

import reflex as rx

from .reflex_local_auth.local_auth import LocalAuthState
from .reflex_local_auth import routes


def links() -> rx.Component:
    """Render the links for the demo."""
    return rx.fragment(
        rx.stack(
            rx.link("User Info", href="/dashboard"),
            rx.link("Leaderboard", href="/leaderboard"),
            rx.link("Games", href="/games"),
            rx.link("Settings", href="/settings"),
            rx.cond(
                LocalAuthState.is_authenticated,
                rx.link(
                    f"Logout ({LocalAuthState.authenticated_user.username})",
                    href="/",
                    on_click=LocalAuthState.do_logout,
                ),
                rx.fragment(
                    rx.link("Login", href=routes.LOGIN_ROUTE),
                    rx.link("Register", href=routes.REGISTER_ROUTE),
                ),
            ),
            flex_direction="row",
        ),
        rx.divider(),
    )


def standard_layout(
    page: rx.Component, heading: str = "RL Competition"
) -> rx.Component:
    """Wrap page with standard layout with header and menu."""
    return rx.fragment(
        rx.vstack(
            rx.heading(heading, font_size="2em"),
            links(),
            page,
            spacing="2",
            padding_top="10%",
            align="center",
        ),
    )
