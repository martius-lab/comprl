"""
Implementation of the data access objects for managing game and user data in SQLite.
"""

from __future__ import annotations

import datetime
import itertools
import os
from typing import Optional, Sequence

import bcrypt
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from comprl.server.data.interfaces import GameEndState, GameResult, UserRole
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

    @staticmethod
    def ranking_order_expression() -> sa.sql.expression.ColumnElement[float]:
        """Get the expression used for ranking users.

        This function can be used in order_by clauses.
        """
        return User.mu - 3 * User.sigma

    def score(self) -> float:
        """Compute the score of the user."""
        return self.mu - 3 * self.sigma


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


def get_ranked_users(session: sa.orm.Session) -> Sequence[User]:
    """Get all users ordered by their score (mu - sigma)."""
    stmt = sa.select(User).order_by(User.ranking_order_expression().desc())
    return session.scalars(stmt).all()


def get_user_pair_statistics(
    session: sa.orm.Session, user_ids: Sequence[int]
) -> dict[tuple[int, int], dict[str, int]]:
    """Get game statistics for all pairs of users.

    Args:
        session: The database session.
        user_ids: The IDs of the users.

    Returns:
        Dictionary mapping pairs of user IDs (given as tuple ``(user_id1, user_id2)`` to
        their game statistics (a dictionary with keys "wins", "losses" and "draws").
    """
    result = {}
    for user_id1, user_id2 in itertools.combinations(user_ids, 2):
        if user_id1 == user_id2:
            continue

        # base statement to count games between user 1 and 2.  Extended in the following
        # by adding more filters to count wins, losses and draws.
        stmt = (
            sa.select(
                sa.func.sum(
                    sa.case(
                        (
                            sa.and_(
                                Game.end_state == GameEndState.WIN,
                                Game.winner == user_id1,
                            ),
                            1,
                        ),
                        else_=0,
                    )
                ).label("wins"),
                sa.func.sum(
                    sa.case(
                        (
                            sa.and_(
                                Game.end_state == GameEndState.WIN,
                                Game.winner != user_id1,
                            ),
                            1,
                        ),
                        else_=0,
                    )
                ).label("losses"),
                sa.func.sum(
                    sa.case(
                        (
                            Game.end_state == GameEndState.DRAW,
                            1,
                        ),
                        else_=0,
                    )
                ).label("draws"),
            )
            .select_from(Game)
            .filter(
                sa.or_(
                    sa.and_(Game.user1 == user_id1, Game.user2 == user_id2),
                    sa.and_(Game.user1 == user_id2, Game.user2 == user_id1),
                )
            )
        )

        res = session.execute(stmt).first()
        if res is None:
            stats = {
                "wins": 0,
                "losses": 0,
                "draws": 0,
            }
        else:
            stats = {
                "wins": res.wins or 0,
                "losses": res.losses or 0,
                "draws": res.draws or 0,
            }

        result[(user_id1, user_id2)] = stats

        # add the reverse pair
        result[(user_id2, user_id1)] = {
            "wins": stats["losses"],
            "losses": stats["wins"],
            "draws": stats["draws"],
        }

    return result


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

    def get_ranked_users(self) -> Sequence[User]:
        """Get all users ordered by their score."""
        with sa.orm.Session(self.engine) as session:
            return get_ranked_users(session)


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
