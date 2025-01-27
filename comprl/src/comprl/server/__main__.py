"""Run the comprl server."""

from __future__ import annotations

import argparse
import datetime
import importlib.abc
import importlib.util
import inspect
import logging
import os
import pathlib
import time
from typing import Type, TYPE_CHECKING

from comprl.server import config, networking
from comprl.server.managers import GameManager, PlayerManager, MatchmakingManager
from comprl.server.interfaces import IPlayer, IServer

if TYPE_CHECKING:
    from comprl.server.interfaces import IGame


log = logging.getLogger("comprl.server")


class Server(IServer):
    """class for server"""

    def __init__(self, game_type: Type[IGame]):
        self.game_manager = GameManager(game_type)
        self.player_manager = PlayerManager()
        self.matchmaking = MatchmakingManager(self.player_manager, self.game_manager)

        self._monitor_log_path = config.get_config().monitor_log_path
        self._monitor_update_interval_s = 10
        self._last_mointor_update = 0

    def on_start(self):
        """gets called when the server starts"""
        log.info("Server started")

    def on_stop(self):
        """gets called when the server stops"""
        log.info("Server stopped")

    def on_connect(self, player: IPlayer):
        """gets called when a player connects"""
        log.info("Player connected | player_id=%s", player.id)
        self.player_manager.add(player)

        def __auth(token):
            if self.player_manager.auth(player.id, token):
                self.matchmaking.try_match(player.id)
                player.notify_info(msg="Authentication successful")
            else:
                player.disconnect("Authentication failed")

        player.authenticate(__auth)

    def on_disconnect(self, player: IPlayer):
        """gets called when a player disconnects"""
        log.info(
            "Player disconnected | user=%s player_id=%s", player.username, player.id
        )
        self.matchmaking.remove(player.id)
        self.player_manager.remove(player)
        self.game_manager.force_game_end(player.id)

    def on_timeout(self, player: IPlayer, failure, timeout):
        """gets called when a player has a timeout"""
        log.info(
            "Player had timeout after %.0f s | user=%s player_id=%s",
            timeout,
            player.username,
            player.id,
        )
        player.disconnect(reason=f"Timeout after {timeout}s")

    def on_remote_error(self, player: IPlayer, error: Exception):
        """gets called when there is an error in deferred"""
        if player.is_connected:
            log.error(
                "Connected player caused remote error | user=%s player_id=%s\n%s",
                player.username,
                player.id,
                error,
            )
        else:
            log.info(
                "Disconnected player caused remote error | user=%s player_id=%s",
                player.username,
                player.id,
            )

    def on_update(self):
        """gets called every update cycle"""
        self.matchmaking.update()
        self._write_monitoring_data()

    def _write_monitoring_data(self):
        if not self._monitor_log_path:
            return

        # only update every _monitor_update_interval_s
        now = time.time()
        if now - self._last_mointor_update < self._monitor_update_interval_s:
            return

        self._last_mointor_update = now
        with open(self._monitor_log_path, "w") as f:

            def plog(*args):
                print(*args, file=f)

            plog(datetime.datetime.now().isoformat(sep=" "))

            n_connected = len(self.player_manager.connected_players)
            plog(f"\nConnected players ({n_connected}):")
            for player in self.player_manager.connected_players.values():
                plog(f"\t{player.username} [{player.id}]")

            n_games = len(self.game_manager.games)
            plog(f"\nGames ({n_games}):")
            for game in self.game_manager.games.values():
                plog(f"\t{game.id} {tuple(str(pid) for pid in game.players)}")

            n_queue = len(self.matchmaking._queue)
            plog(f"\nPlayers in queue ({n_queue}):")
            for entry in self.matchmaking._queue:
                plog(
                    f"\t{entry.user.username} [{entry.player_id}]"
                    f" since {entry.in_queue_since}",
                )

            plog("\nMatch quality scores:")
            for (u1, u2), score in self.matchmaking._match_quality_scores.items():
                plog(f"\t{u1} vs {u2}: {score:0.4f}")

            plog("\nEND")


def load_class(module_path: str, class_name: str):
    """
    Loads a a class from a module.
    """
    # get the module name by splitting the path and removing the file extension
    name = module_path.split(os.sep)[-1].split(".")[0]

    # load the module
    spec = importlib.util.spec_from_file_location(name, module_path)

    # check if the module could be loaded
    if spec is None:
        return None

    # create the module
    module = importlib.util.module_from_spec(spec)

    # this is for mypy
    if not isinstance(spec.loader, importlib.abc.Loader):
        return None

    # exec the module
    try:
        spec.loader.exec_module(module)
    except FileNotFoundError:
        return None

    # finally get the class
    return getattr(module, class_name)


def main():
    """
    Main function to start the server.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=pathlib.Path, help="Config file")
    parser.add_argument("--config-overwrites", type=str, nargs="+", default=[])
    args = parser.parse_args()

    try:
        conf = config.load_config(args.config, args.config_overwrites)
    except Exception as e:
        log.error("Failed to load config: %s", e)
        return

    # set up logging
    logging.basicConfig(
        level=conf.log_level,
        format="[%(asctime)s|%(name)s|%(levelname)s] %(message)s",
    )
    # log = logging.getLogger("comprl.server")

    # resolve relative game_path w.r.t. current working directory
    absolute_game_path = os.path.join(os.getcwd(), conf.game_path)

    # try to load the game class
    game_type = load_class(absolute_game_path, conf.game_class)
    # check if the class could be loaded
    if game_type is None:
        log.error(f"Could not load game class from {absolute_game_path}")
        return
    # check if the class is fully implemented
    if inspect.isabstract(game_type):
        log.error("Provided game class is not valid because it is still abstract.")
        return

    if not conf.data_dir.is_dir():
        log.error("data_dir '%s' not found or not a directory", conf.data_dir)
        return

    server = Server(game_type)
    networking.launch_server(
        server=server, port=conf.port, update_interval=conf.server_update_interval
    )


if __name__ == "__main__":
    main()
