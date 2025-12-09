"""User settings page to change username and password."""

import reflex as rx

from ..components import standard_layout
from ..protected_state import SettingsState
from .. import reflex_local_auth


def change_username_card() -> rx.Component:
    return rx.card(
        rx.heading("Change Login Name", as_="h2", size="4"),
        rx.cond(
            SettingsState.error_message != "",
            rx.callout(
                SettingsState.error_message,
                icon="triangle_alert",
                color_scheme="red",
                role="alert",
                width="100%",
            ),
        ),
        rx.cond(
            SettingsState.status_message != "",
            rx.callout(
                SettingsState.status_message,
                icon="check",
                color_scheme="green",
                role="status",
                width="100%",
            ),
        ),
        rx.form(
            rx.hstack(
                rx.input(
                    name="username",
                    value=SettingsState.username,
                    on_change=SettingsState.set_username,
                    width="100%",
                ),
                rx.hstack(
                    rx.spacer(),
                    rx.button(
                        "Save",
                        type="submit",
                    ),
                ),
                align_items="stretch",
                spacing="3",
            ),
            on_submit=SettingsState.save_username,
        ),
        on_mount=SettingsState.on_load,
    )


@reflex_local_auth.require_login
def settings() -> rx.Component:
    return standard_layout(
        rx.center(change_username_card()),
        heading="User Settings",
    )
