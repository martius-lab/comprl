"""script to reset the game database and the mu and sigma in the user database"""

from comprl.server.data import UserData, GameData
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


def reset_games(game_data: GameData):
    """deletes the game table"""
    game_data.delete_all()
    logging.info("The games table has been deleted.")


def reset_elo(user_data: UserData):
    """reset the elo in the user database: set mu=25.000 and sigma=8.333"""
    user_data.reset_all_matchmaking_parameters()
    logging.info(
        "The matchmaking parameters have been reset to default values for all users."
    )


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

    user_answer = input(
        "Are you sure you want to delete the games table and "
        "reset the matchmaking parameters? (Y/N)"
    )

    if user_answer.lower() == "y":
        game_data = GameData(database_path)
        reset_games(game_data)

        user_data = UserData(database_path)
        reset_elo(user_data)
