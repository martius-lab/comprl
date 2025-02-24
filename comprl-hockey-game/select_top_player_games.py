#!/usr/bin/env python3
"""Select some games from the top players."""

from __future__ import annotations

import argparse
import contextlib
import itertools
import logging
import pathlib
import sys

import sqlalchemy as sa

from comprl.server.data.sql_backend import Game, User
from comprl.server.interfaces import GameEndState


def pick_game(session: sa.orm.Session, user1: User, user2: User) -> Game | None:
    stmt = (
        sa.select(Game)
        .where(
            sa.or_(
                sa.and_(Game.user1 == user1.user_id, Game.user2 == user2.user_id),
                sa.and_(Game.user1 == user2.user_id, Game.user2 == user1.user_id),
            ),
            Game.end_state != GameEndState.DISCONNECTED,
        )
        .order_by(sa.func.random())
        .limit(1)
    )
    return session.scalar(stmt)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database", type=pathlib.Path, help="Database file.")
    parser.add_argument(
        "-n", type=int, default=10, help="Number of top players to consider."
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output."
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="[%(asctime)s] [%(name)s | %(levelname)s] %(message)s",
    )

    if not args.database.exists():
        logging.error(f"{args.database} does not exist.")
        return 1

    engine = sa.create_engine(f"sqlite:///{args.database}")

    # get ranked users
    with sa.orm.Session(engine) as session:
        stmt = sa.select(User).order_by((User.mu - User.sigma).desc()).limit(args.n)
        ranking = session.scalars(stmt).all()

    for user1, user2 in itertools.combinations(ranking, 2):
        with sa.orm.Session(engine) as session:
            game = pick_game(session, user1, user2)
            if game:
                print(
                    ",".join(  # noqa: FLY002
                        [
                            user1.username,
                            user2.username,
                            game.game_id,
                        ]
                    )
                )

    return 0


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        sys.exit(main())
