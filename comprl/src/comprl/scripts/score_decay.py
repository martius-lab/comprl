#!/usr/bin/env python3
"""Slowly increase the sigma rating of users over time.

Periodically increase the sigma rating of all users by a fixed amount.  This is to
penalize users who have not played in a while.  Otherwise a user with a good start could
just stop after few games and keep a good score, while other users might be better in
the meantime.

Increasing sigma of everyone by a fixed amount does not change the ranking (it might
affect matchmaking, though?).  Only users who don't play anymore will slowly move down
in the ranking.
"""

import argparse
import contextlib
import logging
import sys
import time

import sqlalchemy as sa

from comprl.server.config import load_config
from comprl.server.data.sql_backend import User


def adjust_scores(engine: sa.engine.Engine, amount: float) -> None:
    """Adjust the scores of all users."""
    with sa.orm.Session(engine) as session:
        stmt = sa.update(User).values(sigma=User.sigma + amount)
        session.execute(stmt)
        session.commit()


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "config", type=str, help="Config file that specifies the database."
    )
    parser.add_argument(
        "--interval",
        type=int,
        help="Interval (in minutes) at which scores are adjusted. Default: %(default)s",
        default=15,
    )
    parser.add_argument(
        "--amount",
        type=float,
        help="Amount added to sigma in each interval. Default: %(default)s",
        default=0.5,
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output."
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="[%(asctime)s] [%(name)s | %(levelname)s] %(message)s",
    )

    config = load_config(args.config)
    engine = sa.create_engine(f"sqlite:///{config.database_path}")

    interval = args.interval * 60

    while True:
        time.sleep(interval)
        logging.debug("Adjusting scores")
        adjust_scores(engine, args.amount)

    return 0


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        sys.exit(main())
