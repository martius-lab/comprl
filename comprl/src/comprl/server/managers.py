"""
This module contains classes that manage game instances and players.
"""

from __future__ import annotations

import logging
from datetime import datetime
from openskill.models import PlackettLuce
from typing import Type, NamedTuple

import numpy as np

from comprl.server.interfaces import IGame, IPlayer
from comprl.shared.types import GameID, PlayerID
from comprl.server.data import GameData, UserData
from comprl.server.data.sql_backend import User
from comprl.server.data.interfaces import UserRole, GameEndState
from comprl.server.config import get_config


class GameManager:
    """
    A class that manages game instances of a specific game type.

    Attributes:
        games (dict[GameID, IGame]): A dictionary that stores active game instances.
        game_type (Type[IGame]): The type of game to be managed.
    """

    def __init__(self, game_type: Type[IGame]) -> None:
        self.games: dict[GameID, IGame] = {}
        self.game_type = game_type

        self._log = logging.getLogger("comprl.gamemanager")

    def start_game(self, players: list[IPlayer]) -> IGame:
        """
        Starts a new game instance with the given players.

        Args:
            players (list[IPlayer]): A list of players participating in the game.

        Returns:
            GameID: The ID of the newly started game.
        """
        game = self.game_type(players)
        self.games[game.id] = game

        self._log.info(
            "Game started | game_id=%s player1=%s player2=%s",
            game.id,
            players[0].id,
            players[1].id,
        )

        game.add_finish_callback(self.end_game)
        game.start()

        return game

    def end_game(self, game: IGame) -> None:
        """
        Ends the game instance with the specified ID.

        Args:
            game_id (GameID): The ID of the game to be ended.
        """

        if game.id in self.games:
            game_duration = (datetime.now() - game.start_time).total_seconds()
            self._log.debug(
                "Game ended after %.0f s | game_id=%s", game_duration, game.id
            )

            game_result = game.get_result()
            if game_result is not None:
                GameData(get_config().database_path).add(game_result)
            else:
                self._log.error("Game had no valid result | game_id=%s", game.id)
            del self.games[game.id]

    def force_game_end(self, player_id: PlayerID):
        """Forces all games, that a player is currently playing, to end.

        Args:
            player_id (PlayerID): id of the player
        """
        involved_games: list[IGame] = []
        for _, game in self.games.items():
            for game_player_id in game.players:
                if player_id == game_player_id:
                    involved_games.append(game)
                    break
        for game in involved_games:
            self._log.info(
                "Game was forced to end because of a disconnected player"
                " | player_id=%s",
                player_id,
            )
            game.force_end(player_id=player_id)

    def get(self, game_id: GameID) -> IGame | None:
        """
        Retrieves the game instance with the specified ID.

        Args:
            game_id (GameID): The ID of the game to be retrieved.

        Returns:
            Optional[IGame]: The game instance if found, None otherwise.
        """
        return self.games.get(game_id, None)


class PlayerManager:
    """
    Manages connected players.
    """

    def __init__(self) -> None:
        self.auth_players: dict[PlayerID, tuple[IPlayer, int]] = {}
        self.connected_players: dict[PlayerID, IPlayer] = {}

        self._log = logging.getLogger("comprl.playermanager")

    def add(self, player: IPlayer) -> None:
        """
        Adds a player to the manager.

        Args:
            player (IPlayer): The player object to be added.

        Returns:
            None
        """
        self.connected_players[player.id] = player

    def auth(self, player_id: PlayerID, token: str) -> bool:
        """
        Authenticates a player using their player ID and token.

        Args:
            player_id (PlayerID): The ID of the player.
            token (str): The authentication token.

        Returns:
            bool: True if the authentication is successful, False otherwise.
        """
        player = self.connected_players.get(player_id, None)
        # the player might have disconnected?
        if player is None:
            return False

        user = UserData(get_config().database_path).get_user_by_token(token)

        if user is not None:
            # add player to authenticated players
            self.auth_players[player_id] = (
                self.connected_players[player_id],
                user.user_id,
            )
            # set user_id and name of player
            player.user_id = user.user_id
            player.username = user.username
            self._log.info(
                "Player authenticated | user=%s player_id=%s", user.username, player_id
            )
            return True

        return False

    def remove(self, player: IPlayer) -> None:
        """
        Removes a player from the manager.

        Args:
            player (IPlayer): The player object to be removed.

        Returns:
            None
        """
        if player.id in self.connected_players:
            del self.connected_players[player.id]

            if player.id in self.auth_players:
                del self.auth_players[player.id]

    def get_user(self, user_id: int) -> User | None:
        """
        Retrieves a user based on their ID.

        Args:
            user_id (int): The ID of the user.

        Returns:
            Optional[User]: The user object if found, None otherwise.
        """
        return UserData(get_config().database_path).get(user_id)

    def get_user_id(self, player_id: PlayerID) -> int | None:
        """
        Retrieves the user ID associated with a player.

        Args:
            player_id (PlayerID): The ID of the player.

        Returns:
            Optional[int]: The user ID if found, None otherwise.
        """
        if player_id in self.auth_players:
            return self.auth_players[player_id][1]
        return None

    def get_player_by_id(self, player_id: PlayerID) -> IPlayer | None:
        """
        Retrieves the player object associated with a player ID.
        This only works for authenticated players.

        Args:
            player_id (PlayerID): The ID of the player.

        Returns:
            Optional[IPlayer]: The player object if found, None otherwise.
        """
        if player_id in self.auth_players:
            return self.auth_players[player_id][0]
        return None

    def broadcast_error(self, msg: str) -> None:
        """
        Broadcasts a message to all connected players.

        Args:
            msg (str): The message to be broadcasted.

        Returns:
            None
        """

        for player in self.connected_players.values():
            player.notify_error(msg)

    def disconnect_all(self, reason: str) -> None:
        """
        Disconnects all connected players.

        Args:
            reason (str): The reason for disconnection.

        Returns:
            None
        """

        for player in self.connected_players.values():
            player.disconnect(reason)

    def get_matchmaking_parameters(self, user_id: int) -> tuple[float, float]:
        """
        Retrieves the matchmaking parameters of a user based on their ID.

        Args:
            user_id (int): The ID of the user.

        Returns:
            tuple[float, float]: The mu and sigma values of the user.
        """
        return UserData(get_config().database_path).get_matchmaking_parameters(user_id)

    def update_matchmaking_parameters(
        self, user_id: int, new_mu: float, new_sigma: float
    ) -> None:
        """
        Updates the matchmaking parameters of a user based on their ID.

        Args:
            user_id (int): The ID of the user.
            new_mu (float): The new mu value of the user.
            new_sigma (float): The new sigma value of the user.
        """
        UserData(get_config().database_path).set_matchmaking_parameters(
            user_id, new_mu, new_sigma
        )


# Type of a player entry in the queue, containing the player ID, user ID, mu, sigma
# and time they joined the queue
class QueueEntry(NamedTuple):
    """Represents an entry in the matchmaking queue."""

    player_id: PlayerID
    user: User
    in_queue_since: datetime

    def is_legal_match(self, other: QueueEntry) -> bool:
        """Checks if a match with the other player is legal."""
        # prevent the user from playing against himself
        if self.user.user_id == other.user.user_id:
            return False

        # do not match if both players are bots
        if (
            UserRole(self.user.role) == UserRole.BOT
            and UserRole(other.user.role) == UserRole.BOT
        ):
            return False

        return True

    def __str__(self) -> str:
        return (
            f"Player {self.player_id} ({self.user.username}) in queue since"
            f" {self.in_queue_since}"
        )


class MatchmakingManager:
    """handles matchmaking between players and starts the game"""

    def __init__(
        self, player_manager: PlayerManager, game_manager: GameManager
    ) -> None:
        """
        Initializes a MatchmakingManager object.

        Args:
            player_manager (PlayerManager): The player manager object.
            game_manager (GameManager): The game manager object.
        """
        self._log = logging.getLogger("comprl.gamemanager")

        self.player_manager = player_manager
        self.game_manager = game_manager

        config = get_config()

        # queue storing player info and time they joined the queue
        self._queue: list[QueueEntry] = []
        # The model used for matchmaking
        self.model = PlackettLuce()
        self._match_quality_threshold = config.match_quality_threshold
        self._percentage_min_players_waiting = config.percentage_min_players_waiting
        self._percental_time_bonus = config.percental_time_bonus
        self._max_parallel_games = config.max_parallel_games

        # cache matchmaking scores
        self._match_quality_scores: dict[frozenset[str], float] = {}

    def try_match(self, player_id: PlayerID) -> None:
        """
        Tries to add a player with the given player ID to the matchmaking queue.

        Args:
            player_id (PlayerID): The ID of the player to match.

        Returns:
            None
        """
        player = self.player_manager.get_player_by_id(player_id)
        if player is not None:
            # FIXME: we might wan't to kick the player

            def __match(ready: bool):
                if ready:
                    player.notify_info(msg="Waiting in queue")
                    self.match(player_id)

            player.is_ready(result_callback=__match)

    def match(self, player_id: PlayerID) -> None:
        """
        Adds player to the queue.

        Args:
            player_id (PlayerID): The ID of the player to be matched.
        """
        user_id = self.player_manager.get_user_id(player_id)
        if user_id is None:
            self._log.error(
                f"Player {player_id} is not authenticated but tried to queue."
            )
            return
        user = self.player_manager.get_user(user_id)
        if user is None:
            self._log.error(
                (
                    "Failed to add user to queue, user not found in database"
                    " | player_id={%s} user_id={%d}"
                ),
                player_id,
                user_id,
            )
            return

        # check if enough players are waiting
        self._queue.append(QueueEntry(player_id, user, datetime.now()))

        self._log.info(
            "Player added to queue | user=%s role=%s player_id=%s",
            user.username,
            user.role,
            player_id,
        )

        return

    def remove(self, player_id: PlayerID) -> None:
        """
        Removes a player from the matchmaking queue.

        Args:
            player_id (PlayerID): The ID of the player to be removed.
        """
        self._queue = [entry for entry in self._queue if (entry.player_id != player_id)]

    def update(self) -> None:
        """Try to match players in the queue and start games."""
        self._match_quality_scores = {}
        self._search_for_matches()

    def _min_players_waiting(self) -> int:
        """
        Returns the minimum number of players that need to be waiting in the queue.

        Returns:
            int: The minimum number of players.
        """
        return int(
            len(self.player_manager.auth_players) * self._percentage_min_players_waiting
        )

    def _compute_match_qualities(
        self, player1: QueueEntry, candidates: list[QueueEntry]
    ) -> list[tuple[QueueEntry, float]]:
        """
        Computes the match qualities between a player and a list of candidates.

        Args:
            player1: The first player.
            candidates: The list of candidates.

        Returns:
            list[tuple[QueueEntry, float]]: The match qualities.
        """
        return [
            (candidate, self._rate_match_quality(player1, candidate))
            for candidate in candidates
            if player1.is_legal_match(candidate)
        ]

    def _search_for_matches(self) -> None:
        """Search for matches in the queue.

        For each player in the queue, try to find a match with another waiting player.
        If more than one match is possible (i.e. match quality is above the threshold),
        sample from all options with probabilities based on the match qualities.

        If a match is found, directly start a game.
        """
        if len(self._queue) < self._min_players_waiting():
            return

        rng = np.random.default_rng()

        i = 0
        while i < len(self._queue) - 1:
            # stop early if the limit for parallel games is reached
            num_games = len(self.game_manager.games)
            if num_games >= self._max_parallel_games:
                self._log.debug(
                    "Limit for parallel games is reached (running: %d, limit: %d).",
                    num_games,
                    self._max_parallel_games,
                )
                return

            player1 = self._queue[i]
            candidates = self._queue[i + 1 :]

            match_qualities = self._compute_match_qualities(player1, candidates)
            # filter out matches below the quality threshold
            match_qualities = [
                mq for mq in match_qualities if mq[1] > self._match_quality_threshold
            ]

            if match_qualities:
                # separate players and match qualities
                matched_players, matched_qualities = zip(*match_qualities, strict=True)

                # normalize match qualities
                quality_sum = sum(matched_qualities)
                normalised_qualities = [q / quality_sum for q in matched_qualities]

                # sample based on quality
                match_idx = rng.choice(len(match_qualities), p=normalised_qualities)
                matched_player, matched_quality = match_qualities[match_idx]
                self._log.debug(
                    "Matched players %s and %s, quality: %f",
                    player1.player_id,
                    matched_player.player_id,
                    matched_quality,
                )
                self._start_game(player1, matched_player)
            else:
                # Only increment if no match was found.  If a match was found, the entry
                # previously at i has been removed, so the next entry is now at i.
                i += 1

    def _start_game(self, player1: QueueEntry, player2: QueueEntry) -> None:
        """Start a game with the given players."""
        players = [
            self.player_manager.get_player_by_id(player1.player_id),
            self.player_manager.get_player_by_id(player2.player_id),
        ]

        if None in players:
            self._log.error("Player was in queue but not in player manager")
            if players[0] is None:
                self.remove(player1.player_id)
            if players[1] is None:
                self.remove(player2.player_id)
            return

        self.remove(player1.player_id)
        self.remove(player2.player_id)

        game = self.game_manager.start_game(players)  # type: ignore
        game.add_finish_callback(self._end_game)

    def _rate_match_quality(self, player1: QueueEntry, player2: QueueEntry) -> float:
        """
        Rates the match quality between two players.

        Args:
            player1: The first player.
            player2: The second player.

        Returns:
            float: The match quality.
        """
        cache_key = frozenset([player1.user.username, player2.user.username])
        if cache_key in self._match_quality_scores:
            return self._match_quality_scores[cache_key]

        now = datetime.now()
        waiting_time_p1 = (now - player1.in_queue_since).total_seconds()
        waiting_time_p2 = (now - player2.in_queue_since).total_seconds()
        combined_waiting_time = waiting_time_p1 + waiting_time_p2
        # calculate a bonus if the players waited a long time
        waiting_bonus = max(
            0.0, (combined_waiting_time / 60 - 1) * self._percental_time_bonus
        )
        # TODO play with this function. Maybe even use polynomial or exponential growth,
        # depending on waiting time

        rating_p1 = self.model.create_rating(
            [player1.user.mu, player1.user.sigma], "player1"
        )
        rating_p2 = self.model.create_rating(
            [player2.user.mu, player2.user.sigma], "player2"
        )
        draw_prob = self.model.predict_draw([[rating_p1], [rating_p2]])

        match_quality = draw_prob + waiting_bonus

        # log for debugging
        self._match_quality_scores[cache_key] = match_quality

        return match_quality

    def _end_game(self, game: IGame) -> None:
        """Update user ratings and re-add players to the queue.

        Args:
            game: The game that is ending.
        """
        # update elo values
        result = game.get_result()
        # if a player disconnected during the game, simply don't update the ratings
        if result is not None and result.end_state is not GameEndState.DISCONNECTED:
            mu_p1, sigma_p1 = self.player_manager.get_matchmaking_parameters(
                result.user1_id
            )
            mu_p2, sigma_p2 = self.player_manager.get_matchmaking_parameters(
                result.user2_id
            )
            rating_p1 = self.model.create_rating([mu_p1, sigma_p1], "player1")
            rating_p2 = self.model.create_rating([mu_p2, sigma_p2], "player2")
            [[p1], [p2]] = self.model.rate(
                [[rating_p1], [rating_p2]],
                scores=[result.score_user_1, result.score_user_2],
            )
            self.player_manager.update_matchmaking_parameters(
                result.user1_id, p1.mu, p1.sigma
            )
            self.player_manager.update_matchmaking_parameters(
                result.user2_id, p2.mu, p2.sigma
            )

        for _, p in game.players.items():
            self.try_match(p.id)
