"""
This module contains the interfaces for the non-networking logic.
"""

import abc
from typing import Callable, Optional
from datetime import datetime
import numpy as np
import pickle
import logging

from comprl.shared.types import GameID, PlayerID
from comprl.server.util import IDGenerator
from comprl.server.data.interfaces import GameResult, GameEndState
from comprl.server.config import get_config


class IAction:
    """Interface for an action"""

    pass


class IPlayer(abc.ABC):
    """Interface for a player"""

    def __init__(self) -> None:
        self.id: PlayerID = IDGenerator.generate_player_id()
        self.user_id: Optional[int] = None
        self.username: Optional[str] = None
        self.is_connected = True

    @abc.abstractmethod
    def authenticate(self, result_callback):
        """authenticates player

        Args:
            result_callback (Callable): callback
        """
        ...

    @abc.abstractmethod
    def is_ready(self, result_callback) -> bool:
        """checks if the player is ready to play

        Returns:
            bool: returns true if the player is ready to play
        """
        ...

    @abc.abstractmethod
    def notify_start(self, game_id):
        """notifies player that the game has started"""
        ...

    @abc.abstractmethod
    def get_action(self, obv, result_callback) -> IAction:
        """gets an action from the player

        Args:
            obv (Any): observation
            result_callback (Callable): callback

        Returns:
            IAction: action
        """
        ...

    @abc.abstractmethod
    def notify_end(self, result, stats):
        """notifies player that the game has ended"""
        ...

    @abc.abstractmethod
    def disconnect(self, reason: str):
        """disconnect the player"""
        ...

    @abc.abstractmethod
    def notify_error(self, error: str):
        """notifies the player of an error"""
        ...

    @abc.abstractmethod
    def notify_info(self, msg: str):
        """notifies the player of an information"""
        ...


class IGame(abc.ABC):
    """
    Interface for a game.

    Attributes:
        id (GameID):
            The unique identifier of the game.
        players (dict[PlayerID, IPlayer]):
            A dictionary of players participating in the game.
        start_time (datetime):
            The start time of the game.
        finish_callbacks (list[Callable[["IGame"], None]]):
            A list of callbacks to be executed when the game ends.
    """

    @abc.abstractmethod
    def __init__(self, players: list[IPlayer]) -> None:
        """
        Initializes a new instance of the IGame class.

        Args:
            players (list[IPlayer]): A list of players participating in the game.
        """
        self.id: GameID = IDGenerator.generate_game_id()
        self.players = {p.id: p for p in players}
        self.finish_callbacks: list[Callable[["IGame"], None]] = []
        self.scores: dict[PlayerID, float] = {p.id: 0.0 for p in players}
        self.start_time = datetime.now()
        self.disconnected_player_id: PlayerID | None = None
        # dict storing all actions and possible more to be saved later.
        # "actions" is a list of all actions in the game
        self.game_info: dict[str, list[np.ndarray]] = {}
        self.all_actions: list[np.ndarray] = []
        # When writing a game class you can fill the dict game_info with more
        # information

    def add_finish_callback(self, callback: Callable[["IGame"], None]) -> None:
        """
        Adds a callback function to be executed when the game ends.

        Args:
            callback (Callable[["IGame"], None]): The callback function to be added.
        """
        self.finish_callbacks.append(callback)

    def start(self):
        """
        Notifies all players that the game has started and starts the game cycle.
        """
        self.start_time = datetime.now()

        for player in self.players.values():
            player.notify_start(self.id)

        self._run()

    def _end(self, reason="unknown"):
        """
        Notifies all players that the game has ended and writes all actions in a file.

        Args:
            reason (str): The reason why the game has ended. Defaults to "unknown".
        """
        if self.disconnected_player_id is None:
            # store actions:
            try:
                # TODO: maybe add multithreading here to ease the load on the main
                # server thread as storing the actions can take a while
                self.game_info["actions"] = np.array(self.all_actions)

                data_dir = get_config().data_dir
                # should already be checked during config loading but just to be sure
                assert data_dir.is_dir(), f"data_dir '{data_dir}' is not a directory"
                game_actions_dir = data_dir / "game_actions"
                game_actions_dir.mkdir(exist_ok=True)
                output_file = game_actions_dir / f"{self.id}.pkl"

                logging.debug("Save game actions to %s", output_file)
                with open(output_file, "wb") as f:
                    pickle.dump(self.game_info, f)
            except Exception as e:
                logging.error(
                    "Error while saving game actions: %s | game_id=%s", e, self.id
                )

        # notify end
        for callback in self.finish_callbacks:
            callback(self)

        for player in self.players.values():
            if player.id == self.disconnected_player_id:
                continue
            player.notify_end(
                self._player_won(player.id), self._player_stats(player.id)
            )

    def _run(self):
        """
        Collects all actions and puts them in the current_actions list.
        """
        actions = {}
        for p in self.players.values():

            def _res(value, id=p.id):
                if not self._validate_action(value):
                    self.players[id].disconnect("Invalid action")
                actions[id] = value
                if len(actions) == len(self.players):
                    # all players have submitted their actions
                    # update the game, and if the game is over, end it
                    if self.disconnected_player_id is not None:
                        return
                    self.all_actions.append([actions[p] for p in actions])
                    if not self._update(actions):
                        self._run()
                    else:
                        self._end(reason="Player won")

            p.get_action(self._get_observation(p.id), _res)

    def force_end(self, player_id: PlayerID):
        """forces the end of the game. Should be used when a player disconnects.

        Args:
            player_id (PlayerID): the player that caused the forced end (disconnected)
        """
        self.disconnected_player_id = player_id
        self._end(reason="Player disconnected")

    def get_result(self) -> GameResult | None:
        """
        Returns the result of the game.

        Returns:
            GameResult: The result of the game.
        """
        player_ids = list(self.players.keys())

        game_end_state = GameEndState.DRAW
        if self._player_won(player_ids[0]) or self._player_won(player_ids[1]):
            game_end_state = GameEndState.WIN
        if self.disconnected_player_id is not None:
            game_end_state = GameEndState.DISCONNECTED

        user1_id = self.players[player_ids[0]].user_id
        user2_id = self.players[player_ids[1]].user_id

        if user1_id is None or user2_id is None:
            return None

        return GameResult(
            game_id=self.id,
            user1_id=user1_id,
            user2_id=user2_id,
            score_user_1=self.scores[player_ids[0]],
            score_user_2=self.scores[player_ids[1]],
            start_time=self.start_time,
            end_state=game_end_state,
            is_user1_winner=self._player_won(player_ids[0]),
            is_user1_disconnected=(self.disconnected_player_id == player_ids[0]),
        )

    @abc.abstractmethod
    def _update(self, actions: dict[PlayerID, list[float]]) -> bool:
        """
        Updates the game with the players' actions.

        Returns:
            bool: True if the game is over, False otherwise.
        """
        return False

    @abc.abstractmethod
    def _validate_action(self, action) -> bool:
        """
        Checks whether an action is valid.

        Args:
            action: The action to be validated.

        Returns:
            bool: True if the action is valid, False otherwise.
        """
        ...

    @abc.abstractmethod
    def _get_observation(self, id: PlayerID) -> list[float]:
        """
        Returns the observation for the player.

        Args:
            id (PlayerID): The ID of the player for which the observation is requested.

        Returns:
            list[float]: The observation for the player.
        """
        ...

    @abc.abstractmethod
    def _player_won(self, id: PlayerID) -> bool:
        """
        Checks whether the player has won.

        Args:
            id (PlayerID): The ID of the player to be checked.

        Returns:
            bool: True if the player has won, False otherwise.
        """
        ...

    @abc.abstractmethod
    def _player_stats(self, id: PlayerID) -> list[float]:
        """
        Returns all stats that should be sent to the player if the game has ended.

        Args:
            id (PlayerID): The ID of the player.

        Returns:
            int: The result of the player.
        """
        ...


class IServer:
    """
    Interface for the server.

    This interface defines the methods that a server implementation should provide.
    """

    @abc.abstractmethod
    def on_start(self):
        """
        Gets called when the server starts.
        """
        ...

    @abc.abstractmethod
    def on_stop(self):
        """
        Gets called when the server stops.
        """
        ...

    @abc.abstractmethod
    def on_connect(self, player: IPlayer):
        """
        Gets called when a player connects.
        Args:
            player (IPlayer): The player that has connected.
        """
        ...

    @abc.abstractmethod
    def on_disconnect(self, player: IPlayer):
        """
        Gets called when a player disconnects.
        Args:
            player (IPlayer): The player that has disconnected.
        """
        ...

    @abc.abstractmethod
    def on_timeout(self, player: IPlayer, failure, timeout):
        """
        Gets called when a player has a timeout.
        Args:
            player (IPlayer): The player that has a timeout.
        """
        ...

    @abc.abstractmethod
    def on_remote_error(self, player: IPlayer, error):
        """
        Gets called when an error in deferred occurs.
        Args:
            player (IPlayer): The player that caused the error.
            error (Exception): Error that occurred
        """
        ...

    @abc.abstractmethod
    def on_update(self):
        """
        Gets called when the server updates.
        Frequency depends on the final implementation.
        """
        ...
