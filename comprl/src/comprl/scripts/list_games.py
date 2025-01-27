#!/usr/bin/env python3
"""List all finished games."""

import argparse
import contextlib
import logging
import sys

import sqlalchemy as sa
import tabulate

from comprl.server.config import load_config
from comprl.server.data.sql_backend import Game
from comprl.server.data.interfaces import GameEndState


def main() -> int:
    """Entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "config", type=str, help="Config file that specifies the databases."
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output."
    )
    parser.add_argument("--id", action="store_true", help="Show game IDs")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="[%(asctime)s] [%(name)s | %(levelname)s] %(message)s",
    )

    config = load_config(args.config)
    engine = sa.create_engine(f"sqlite:///{config.database_path}")

    fields = [
        "start_time",
        "user1",
        "user2",
        "score1",
        "score2",
        "end_state",
        "winner",
        "disconnected",
    ]

    if args.id:
        fields = ["game_id"] + fields

    table_data = []
    with sa.orm.Session(engine) as session:
        for game in session.scalars(sa.select(Game)).all():
            game_data = {
                "start_time": game.start_time,
                "user1": game.user1_.username,
                "user2": game.user2_.username,
                "score1": game.score1,
                "score2": game.score2,
                "end_state": GameEndState(game.end_state).name,
                "winner": game.winner_.username if game.winner_ is not None else None,
                "disconnected": (
                    game.disconnected_.username
                    if game.disconnected_ is not None
                    else None
                ),
            }

            if args.id:
                game_data["game_id"] = game.game_id

            table_data.append([game_data[field] for field in fields])

    print(tabulate.tabulate(table_data, headers=fields))

    return 0


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        sys.exit(main())
