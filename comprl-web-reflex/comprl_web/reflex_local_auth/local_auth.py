"""
Authentication data is stored in the LocalAuthState class so that all substates can
access it for verifying access to event handlers and computed vars.

Your app may inherit from LocalAuthState, or it may access it via the `get_state` API.
"""

from __future__ import annotations

import datetime

import sqlalchemy as sa
import reflex as rx

from comprl.server.data.sql_backend import User

from .. import config
from .auth_session import LocalAuthSession

AUTH_TOKEN_LOCAL_STORAGE_KEY = "_auth_token"
DEFAULT_AUTH_SESSION_EXPIRATION_DELTA = datetime.timedelta(days=7)
DEFAULT_AUTH_REFRESH_DELTA = datetime.timedelta(minutes=10)


# TODO move to other module?
def get_session() -> sa.orm.Session:
    db_url = f"sqlite:///{config.get_config().database_path}"
    engine = sa.create_engine(db_url)
    return sa.orm.Session(engine)


NONE_USER = User(username="", password=b"", token="")


class LocalAuthState(rx.State):
    # The auth_token is stored in local storage to persist across tab and browser
    # sessions.
    auth_token: str = rx.LocalStorage(name=AUTH_TOKEN_LOCAL_STORAGE_KEY)

    @rx.var(cache=True, initial_value=NONE_USER)
    def authenticated_user(self) -> User:
        """The currently authenticated user.

        Returns:
            User instance corresponding to the currently authenticated user or None if
            no user is authenticated.
        """
        with get_session() as session:
            result = session.scalars(
                sa.select(User, LocalAuthSession).where(
                    LocalAuthSession.session_id == self.auth_token,
                    LocalAuthSession.expiration
                    >= datetime.datetime.now(datetime.timezone.utc),
                    User.user_id == LocalAuthSession.user_id,
                ),
            ).first()
            if result:
                return result
        return NONE_USER

    @rx.var(cache=True, interval=DEFAULT_AUTH_REFRESH_DELTA)
    def is_authenticated(self) -> bool:
        """Whether the current user is authenticated.

        Returns:
            True if the authenticated user has a positive user ID, False otherwise.
        """
        return self.authenticated_user.user_id is not None

    def do_logout(self) -> None:
        """Destroy LocalAuthSessions associated with the auth_token."""
        with get_session() as session:
            for auth_session in session.scalars(
                sa.select(LocalAuthSession).where(
                    LocalAuthSession.session_id == self.auth_token
                )
            ).all():
                session.delete(auth_session)
            session.commit()
        self.auth_token = self.auth_token

    def _login(
        self,
        user_id: int,
        expiration_delta: datetime.timedelta = DEFAULT_AUTH_SESSION_EXPIRATION_DELTA,
    ) -> None:
        """Create an LocalAuthSession for the given user_id.

        If the auth_token is already associated with an LocalAuthSession, it will be
        logged out first.

        Args:
            user_id: The user ID to associate with the LocalAuthSession.
            expiration_delta: The amount of time before the LocalAuthSession expires.
        """
        self.do_logout()
        if user_id < 0:
            return
        self.auth_token = self.auth_token or self.router.session.client_token
        with get_session() as session:
            session.add(
                LocalAuthSession(  # type: ignore
                    user_id=user_id,
                    session_id=self.auth_token,
                    expiration=datetime.datetime.now(datetime.timezone.utc)
                    + expiration_delta,
                )
            )
            session.commit()
