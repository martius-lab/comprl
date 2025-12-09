#!/usr/bin/env python3
"""Create the database for a given configuration."""

import argparse
import contextlib
import logging
import pathlib
import sys

from comprl.server.data.models import create_database_tables

try:
    import tomllib  # type: ignore[import-not-found]
except ImportError:
    # tomllib was added in Python 3.11.  Older versions can use tomli
    import tomli as tomllib  # type: ignore[import-not-found, no-redef]


def main() -> int:
    """main."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "config", type=pathlib.Path, help="Path to the configuration file."
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output."
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="[%(asctime)s] [%(name)s | %(levelname)s] %(message)s",
    )

    with open(args.config, "rb") as f:
        config = tomllib.load(f)["comprl"]

    db_path = config["database_path"]

    if pathlib.Path(db_path).exists():
        print(f"ERROR: Database '{db_path}' already exists.", file=sys.stderr)
        return 1
    create_database_tables(db_path)

    return 0


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        sys.exit(main())
