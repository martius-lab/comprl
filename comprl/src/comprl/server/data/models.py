"""Database models."""

from __future__ import annotations

import datetime
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship


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
    token: Mapped[str] = mapped_column(sa.String(64), unique=True)
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


def create_database_tables(db_path: str) -> None:
    """Create the database tables in the given SQLite database."""
    engine = sa.create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
