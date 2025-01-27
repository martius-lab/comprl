"""Configuration settings for the server."""

import dataclasses
import pathlib
import os
from typing import Optional

try:
    import tomllib  # type: ignore[import-not-found]
except ImportError:
    # tomllib was added in Python 3.11.  Older versions can use tomli
    import tomli as tomllib  # type: ignore[import-not-found, no-redef]

import omegaconf
import variconf


@dataclasses.dataclass
class Config:
    """Configuration settings."""

    #: Port to listen on
    port: int = 8080
    #: Update interval for the matchmaking
    server_update_interval: float = 1.0
    #: Seconds to wait for a player to answer
    timeout: int = 10
    #: Log level used by the server
    log_level: str = "INFO"
    #: File containing the game class to run
    game_path: pathlib.Path = omegaconf.MISSING
    #: Class name of the game
    game_class: str = omegaconf.MISSING
    #: Path to the database file
    database_path: pathlib.Path = omegaconf.MISSING
    #: Path to the data directory (used to save data like game actions)
    data_dir: pathlib.Path = omegaconf.MISSING
    #: Threshold for matching players
    match_quality_threshold: float = 0.8
    #: Percentage of players always waiting in queue
    percentage_min_players_waiting: float = 0.1
    #: (Minutes waiting * percentage) added as a time bonus for waiting players
    percental_time_bonus: float = 0.1
    #: Maximum number of games that can be played in parallel
    max_parallel_games: int = 100

    #: File to which monitoring information is written.  Ideally use a in-memory file
    #: (e.g. in /dev/shm).
    monitor_log_path: Optional[pathlib.Path] = None

    #: Key that has to be specified to register
    registration_key: str = ""
    #: URL of the competition server
    server_url: str = "comprl.example.com"


_config: Config | None = None


def get_config() -> Config:
    """Get global config instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config


def set_config(config: Config):
    """Set global config instance."""
    global _config
    _config = config


def load_config(
    config_file: str | os.PathLike, dotlist_overwrites: list[str] | None = None
) -> Config:
    """Load config from config file and optional dotlist overwrites."""
    if dotlist_overwrites is None:
        dotlist_overwrites = []

    config_file = pathlib.Path(config_file)

    wconf = variconf.WConf(Config)

    with open(config_file, "rb") as f:
        config_from_file = tomllib.load(f)["CompetitionServer"]

    _config = wconf.load_dict(config_from_file).load_dotlist(dotlist_overwrites)
    config = Config(**_config.get())  # type: ignore[arg-type]

    # resolve relative paths w.r.t config file location
    config_file_dir = config_file.parent
    config.game_path = config_file_dir / config.game_path
    config.database_path = config_file_dir / config.database_path
    config.data_dir = config_file_dir / config.data_dir

    set_config(config)

    return get_config()
