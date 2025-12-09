"""Script to add dummy user to the user database."""

from comprl.server.data import UserData, init_engine
import logging
import argparse

try:
    import tomllib  # type: ignore[import-not-found]
except ImportError:
    # tomllib was added in Python 3.11.  Older versions can use tomli
    import tomli as tomllib  # type: ignore[import-not-found, no-redef]

# run with python -m comprl.scripts.dummy_user

logging.basicConfig(level=logging.DEBUG)


def insert_users():
    """inserts four dummy user to the user database"""
    UserData.add(user_name="test1", user_password="password1", user_token="token1")
    UserData.add(user_name="test2", user_password="password2", user_token="token2")
    UserData.add(user_name="test3", user_password="password3", user_token="token3")
    UserData.add(user_name="test4", user_password="password4", user_token="token4")

    logging.info("Four dummy users have been added.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="The following arguments are supported:"
    )
    parser.add_argument("--config", type=str, help="Config file")
    parser.add_argument("--database-path", type=str, help="Path to the database file")
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

    init_engine(database_path)
    insert_users()
