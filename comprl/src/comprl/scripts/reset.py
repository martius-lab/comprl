"""Reset user scores and delete all games from the database."""

from comprl.server.data import UserData, GameData, init_engine
import logging
import argparse
import os
import sys

try:
    import tomllib  # type: ignore[import-not-found]
except ImportError:
    # tomllib was added in Python 3.11.  Older versions can use tomli
    import tomli as tomllib  # type: ignore[import-not-found, no-redef]

# run with python -m comprl.scripts.reset

logging.basicConfig(level=logging.DEBUG)


def reset_games():
    """deletes the game table"""
    GameData.delete_all()
    logging.info("Cleared games table.")


def reset_elo():
    """Reset the mu/sigma score of all users to default values"""
    UserData.reset_all_ratings()
    logging.info("Reset matchmaking parameters to default values.")
    logging.info("Cleared rating change log.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="The following arguments are supported:"
    )
    parser.add_argument("--config", type=str, help="Config file")
    parser.add_argument(
        "--database-path",
        type=str,
        help="Path to the database file (doesn't have to exist)",
    )
    args = parser.parse_args()

    data = None
    if args.config is not None:
        # load config file
        with open(args.config, "rb") as f:
            data = tomllib.load(f)["comprl"]

    if args.database_path:
        database_path = args.database_path
    elif data:
        database_path = data["database_path"]
    else:
        parser.error("Need to provide either --config or --database-path")

    if not os.path.exists(database_path):
        print(f"Database file {database_path} does not exist.")
        sys.exit(1)

    init_engine(database_path)

    user_answer = input(
        "Are you sure you want to delete the games table and "
        "reset the matchmaking parameters? (Y/n) "
    )

    if user_answer.lower() == "y":
        reset_games()
        reset_elo()
