"""Login state and authentication logic."""

from __future__ import annotations

import bcrypt
import reflex as rx
from sqlalchemy import select

from comprl.server.data.sql_backend import User

from . import routes
from .local_auth import LocalAuthState, get_session


def verify_password(user_password_hash: bytes, secret: str) -> bool:
    """Validate the user's password.

    Args:
        secret: The password to check.

    Returns:
        True if the hashed secret matches this user's password_hash.
    """
    return bcrypt.checkpw(
        password=secret.encode("utf-8"),
        hashed_password=user_password_hash,
    )


class LoginState(LocalAuthState):
    """
    Handle login form submission and redirect to proper routes after authentication.
    """

    error_message: str = ""
    redirect_to: str = ""

    def on_submit(self, form_data) -> rx.event.EventSpec:
        """Handle login form on_submit.

        Args:
            form_data: A dict of form fields and values.
        """
        self.error_message = ""
        username = form_data["username"]
        password = form_data["password"]

        with get_session() as session:
            user = session.scalars(
                select(User).where(User.username == username)
            ).one_or_none()

        # FIXME
        # if user is not None and not user.enabled:
        #    self.error_message = "This account is disabled."
        #    return rx.set_value("password", "")

        if (
            user is not None
            and user.user_id is not None
            # and user.enabled  # FIXME
            and password
            and verify_password(user.password, password)
        ):
            # mark the user as logged in
            self._login(user.user_id)
        else:
            self.error_message = "There was a problem logging in, please try again."
            return rx.set_value("password", "")

        self.error_message = ""
        return LoginState.redir()  # type: ignore

    def redir(self) -> rx.event.EventSpec | None:
        """Redirect to redirect_to if logged in, or to the login page if not."""
        if not self.is_hydrated:
            # wait until after hydration to ensure auth_token is known
            return LoginState.redir()  # type: ignore
        page = self.router.url.path
        if not self.is_authenticated and page != routes.LOGIN_ROUTE:
            self.redirect_to = page
            return rx.redirect(routes.LOGIN_ROUTE)
        elif self.is_authenticated and page == routes.LOGIN_ROUTE:
            return rx.redirect(self.redirect_to or "/")

        return None


def require_login(page: rx.app.ComponentCallable) -> rx.app.ComponentCallable:
    """Decorator to require authentication before rendering a page.

    If the user is not authenticated, then redirect to the login page.

    Args:
        page: The page to wrap.

    Returns:
        The wrapped page component.
    """

    def protected_page():
        return rx.fragment(
            rx.cond(
                LoginState.is_hydrated & LoginState.is_authenticated,  # type: ignore
                page(),
                rx.center(
                    # When this text mounts, it will redirect to the login page
                    rx.text("Loading...", on_mount=LoginState.redir),
                ),
            )
        )

    protected_page.__name__ = page.__name__
    return protected_page
