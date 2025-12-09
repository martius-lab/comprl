"""User settings page to change username and password."""

import reflex as rx

from ..components import standard_layout
from ..protected_state import SettingsState
from .. import reflex_local_auth


def change_username_card() -> rx.Component:
    return rx.card(
        rx.heading("Change Login Name", as_="h2", size="4"),
        rx.cond(
            SettingsState.username_error_message != "",
            rx.callout(
                SettingsState.username_error_message,
                icon="triangle_alert",
                color_scheme="red",
                role="alert",
                width="100%",
            ),
        ),
        rx.cond(
            SettingsState.username_status_message != "",
            rx.callout(
                SettingsState.username_status_message,
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
        width="100%",
    )


def change_password_card() -> rx.Component:
    return rx.card(
        rx.heading("Change Password", as_="h2", size="4"),
        rx.spacer(height="0.5rem"),
        rx.cond(
            SettingsState.password_error_message != "",
            rx.callout(
                SettingsState.password_error_message,
                icon="triangle_alert",
                color_scheme="red",
                role="alert",
                width="100%",
            ),
        ),
        rx.cond(
            SettingsState.password_status_message != "",
            rx.callout(
                SettingsState.password_status_message,
                icon="check",
                color_scheme="green",
                role="status",
                width="100%",
            ),
        ),
        rx.form(
            rx.vstack(
                rx.text("Current Password:"),
                rx.input(
                    name="current_password",
                    value=SettingsState.current_password,
                    on_change=SettingsState.set_current_password,
                    type="password",
                    width="100%",
                ),
                rx.text("New Password:"),
                rx.input(
                    name="new_password",
                    value=SettingsState.new_password,
                    on_change=SettingsState.set_new_password,
                    type="password",
                    placeholder="min. 8 characters",
                    width="100%",
                ),
                rx.text("Confirm New Password:"),
                rx.input(
                    name="confirm_password",
                    value=SettingsState.confirm_password,
                    on_change=SettingsState.set_confirm_password,
                    type="password",
                    width="100%",
                ),
                rx.button(
                    "Update password",
                    type="submit",
                ),
                spacing="1",
            ),
            on_submit=SettingsState.save_password,
        ),
        width="100%",
    )


@reflex_local_auth.require_login
def settings() -> rx.Component:
    return standard_layout(
        rx.center(
            rx.vstack(
                change_username_card(),
                change_password_card(),
                spacing="4",
                width="100%",
                max_width="36rem",
            ),
            on_mount=SettingsState.on_load,
        ),
        heading="User Settings",
    )
