"""
Implementation of the data access objects for managing game and user data in SQLite.
"""

from __future__ import annotations

import datetime
import os
from typing import Optional, Sequence

import bcrypt
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from comprl.server.data.interfaces import GameResult, UserRole
from comprl.server.config import get_config


DEFAULT_MU = 25.0
DEFAULT_SIGMA = 8.333


class Base(sa.orm.MappedAsDataclass, sa.orm.DeclarativeBase):
    """Base class for all ORM classes."""


class User(Base):
    """A User."""

    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(init=False, primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    password: Mapped[bytes] = mapped_column()
    token: Mapped[str] = mapped_column(sa.String(64))
    role: Mapped[str] = mapped_column(default="user")
    mu: Mapped[float] = mapped_column(default=DEFAULT_MU)
    sigma: Mapped[float] = mapped_column(default=DEFAULT_SIGMA)


class Game(Base):
    """Games."""

    __tablename__ = "games"

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    game_id: Mapped[str] = mapped_column(unique=True)

    user1: Mapped[int] = mapped_column(sa.ForeignKey("users.user_id"))
    user2: Mapped[int] = mapped_column(sa.ForeignKey("users.user_id"))
    user1_: Mapped["User"] = relationship(init=False, foreign_keys=[user1])
    user2_: Mapped["User"] = relationship(init=False, foreign_keys=[user2])

    score1: Mapped[float]
    score2: Mapped[float]
    start_time: Mapped[datetime.datetime] = mapped_column(sa.DateTime)
    end_state: Mapped[int]

    winner: Mapped[Optional[int]] = mapped_column(sa.ForeignKey("users.user_id"))
    winner_: Mapped["User"] = relationship(init=False, foreign_keys=[winner])
    disconnected: Mapped[Optional[int]] = mapped_column(sa.ForeignKey("users.user_id"))
    disconnected_: Mapped["User"] = relationship(
        init=False, foreign_keys=[disconnected]
    )


class GameData:
    """Represents a data access object for managing game data in a SQLite database."""

    def __init__(self, db_path: str | os.PathLike) -> None:
        db_url = f"sqlite:///{db_path}"
        self.engine = sa.create_engine(db_url)

    def add(self, game_result: GameResult) -> None:
        """
        Adds a game result to the database.

        Args:
            db_path: Path to the sqlite database.

        """
        with sa.orm.Session(self.engine) as session:
            game = Game(
                game_id=str(game_result.game_id),
                user1=game_result.user1_id,
                user2=game_result.user2_id,
                score1=game_result.score_user_1,
                score2=game_result.score_user_2,
                start_time=game_result.start_time,
                end_state=int(game_result.end_state),
                winner=game_result.winner_id,
                disconnected=game_result.disconnected_id,
            )
            session.add(game)
            session.commit()

    def get_all(self) -> Sequence[Game]:
        """
        Retrieves all games from the database.

        Returns:
            list[Game]: A list of all games.
        """
        with sa.orm.Session(self.engine) as session:
            return session.scalars(sa.select(Game)).all()

    def delete_all(self) -> None:
        """Delete all games."""
        with sa.orm.Session(self.engine) as session:
            session.query(Game).delete()
            session.commit()


class UserData:
    """Represents a data access object for managing game data in a SQLite database."""

    def __init__(self, db_path: str | os.PathLike | None = None) -> None:
        """
        Initializes a new instance of the UserData class.

        Args:
            db_path: Path to the sqlite database.
        """
        if db_path is None:
            db_path = get_config().database_path

        # connect to the database
        db_url = f"sqlite:///{db_path}"
        self.engine = sa.create_engine(db_url)

    def add(
        self,
        user_name: str,
        user_password: str,
        user_token: str,
        user_role=UserRole.USER,
        user_mu=DEFAULT_MU,
        user_sigma=DEFAULT_SIGMA,
    ) -> int:
        """
        Adds a new user to the database.

        Args:
            user_name: The name of the user.
            user_password: The password of the user.
            user_token: The token of the user.
            user_role: The role of the user.
            Defaults to UserRole.USER.
            user_mu: The mu value of the user.
            user_sigma: The sigma value of the user.

        Returns:
            int: The ID of the newly added user.
        """
        with sa.orm.Session(self.engine) as session:
            user = User(
                username=user_name,
                password=hash_password(user_password),
                token=user_token,
                role=user_role.value,
                mu=user_mu,
                sigma=user_sigma,
            )
            session.add(user)
            session.commit()
            session.refresh(user)

            return user.user_id

    def get(self, user_id: int) -> User:
        """Get user with the specified ID."""
        with sa.orm.Session(self.engine) as session:
            user = session.get(User, user_id)

        if user is None:
            raise ValueError(f"User with ID {user_id} not found.")

        return user

    def get_user_by_token(self, access_token: str) -> User | None:
        """Retrieves a user based on their access token.

        Args:
            access_token: The access token of the user.

        Returns:
            User instance or None if no user with the given token is found.
        """
        with sa.orm.Session(self.engine) as session:
            user = session.query(User).filter(User.token == access_token).first()
            return user

    def get_matchmaking_parameters(self, user_id: int) -> tuple[float, float]:
        """
        Retrieves the matchmaking parameters of a user based on their ID.

        Args:
            user_id (int): The ID of the user.

        Returns:
            tuple[float, float]: The mu and sigma values of the user.
        """
        with sa.orm.Session(self.engine) as session:
            user = session.get(User, user_id)
            if user is None:
                raise ValueError(f"User with ID {user_id} not found.")

            return user.mu, user.sigma

    def set_matchmaking_parameters(self, user_id: int, mu: float, sigma: float) -> None:
        """
        Sets the matchmaking parameters of a user based on their ID.

        Args:
            user_id (int): The ID of the user.
            mu (float): The new mu value of the user.
            sigma (float): The new sigma value of the user.
        """
        with sa.orm.Session(self.engine) as session:
            user = session.get(User, user_id)
            if user is None:
                raise ValueError(f"User with ID {user_id} not found.")

            user.mu = mu
            user.sigma = sigma
            session.commit()

    def reset_all_matchmaking_parameters(self) -> None:
        """Resets the matchmaking parameters of all users."""
        with sa.orm.Session(self.engine) as session:
            session.query(User).update({"mu": DEFAULT_MU, "sigma": DEFAULT_SIGMA})
            session.commit()


def hash_password(secret: str) -> bytes:
    """Hash the secret using bcrypt.

    Args:
        secret: The password to hash.

    Returns:
        The hashed password.
    """
    return bcrypt.hashpw(
        password=secret.encode("utf-8"),
        salt=bcrypt.gensalt(),
    )


def create_database_tables(db_path: str) -> None:
    """Create the database tables in the given SQLite database."""
    engine = sa.create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
