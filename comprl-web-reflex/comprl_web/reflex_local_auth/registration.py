"""New user registration validation and database logic."""

from __future__ import annotations

import asyncio
import re

import reflex as rx

from sqlalchemy import select

from comprl.server.util import IDGenerator
from comprl.server.data.sql_backend import User, hash_password

from ..config import get_config
from . import routes
from .local_auth import LocalAuthState, get_session


POST_REGISTRATION_DELAY = 0.5
PASSWORD_MIN_LENGTH = 8


def generate_access_token() -> str:
    """Generate a random access token."""
    return str(IDGenerator.generate_player_id())


def validate_username(username: str) -> bool:
    """Validate the username against allowed characters."""
    return re.match(r"^[a-zA-Z0-9_-]+$", username) is not None


class RegistrationState(LocalAuthState):
    """Handle registration form submission and redirect to login page afterwards."""

    success: bool = False
    error_message: str = ""
    new_user_id: int = -1

    def _validate_fields(
        self, registration_key: str, username: str, password: str, confirm_password: str
    ) -> rx.event.EventSpec | list[rx.event.EventSpec] | None:
        if registration_key != get_config().registration_key:
            self.error_message = "Invalid registration key"
            return rx.set_focus("key")

        if not username:
            self.error_message = "Username cannot be empty"
            return rx.set_focus("username")

        if not validate_username(username):
            self.error_message = (
                "Username contains invalid characters."
                "  Allowed characters are: a-Z0-9_-"
            )
            return rx.set_focus("username")

        with get_session() as session:
            existing_user = session.scalars(
                select(User).where(User.username == username)
            ).one_or_none()

        if existing_user is not None:
            self.error_message = (
                f"Username {username} is already registered. Try a different name"
            )
            return [rx.set_value("username", ""), rx.set_focus("username")]

        if len(password) < PASSWORD_MIN_LENGTH:
            self.error_message = (
                f"Password needs to be at least {PASSWORD_MIN_LENGTH} characters long"
            )
            return rx.set_focus("password")

        if password != confirm_password:
            self.error_message = "Passwords do not match"
            return [
                rx.set_value("confirm_password", ""),
                rx.set_focus("confirm_password"),
            ]

        return None

    def _register_user(self, username: str, password: str) -> None:
        """Create the new user and add it to the database."""
        # TODO better use UserData.add_user() here, to avoid redundant code
        with get_session() as session:
            new_user = User(
                username=username,
                password=hash_password(password),
                token=generate_access_token(),
                # enabled=True,  # FIXME
            )

            session.add(new_user)
            session.commit()
            session.refresh(new_user)
            self.new_user_id = new_user.user_id

    def handle_registration(
        self, form_data
    ) -> rx.event.EventSpec | list[rx.event.EventSpec]:
        """Handle registration form on_submit.

        Set error_message appropriately based on validation results.

        Args:
            form_data: A dict of form fields and values.
        """
        username = form_data["username"]
        password = form_data["password"]
        validation_errors = self._validate_fields(
            form_data["key"], username, password, form_data["confirm_password"]
        )
        if validation_errors:
            self.new_user_id = -1
            return validation_errors

        self._register_user(username, password)
        return type(self).successful_registration

    async def successful_registration(self):
        """Set success and redirect to login page after a brief delay."""
        self.error_message = ""
        self.new_user_id = -1
        self.success = True
        yield

        await asyncio.sleep(POST_REGISTRATION_DELAY)
        yield [rx.redirect(routes.LOGIN_ROUTE), RegistrationState.set_success(False)]

    def redir(self):
        """Redirect to the registration form."""
        return rx.redirect(routes.REGISTER_ROUTE)
