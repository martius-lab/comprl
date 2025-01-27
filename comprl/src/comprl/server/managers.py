"""
This module contains classes that manage game instances and players.
"""

import logging
from datetime import datetime
from openskill.models import PlackettLuce
from typing import Type, NamedTuple

from comprl.server.interfaces import IGame, IPlayer
from comprl.shared.types import GameID, PlayerID
from comprl.server.data import GameData, UserData
from comprl.server.data.sql_backend import User
from comprl.server.data.interfaces import UserRole
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
            # set user_id of player
            player.user_id = user.user_id
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

    def __str__(self) -> str:
        return (
            f"Player {self.player_id} ({self.user.username}) joined the queue at"
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

    def _update(self) -> None:
        self._match_quality_scores: list[tuple[str, str, float]] = []

        # TODO: don't print to stdout but to shared memory file?
        # print("Players in queue:")
        # for entry in self._queue:
        #     print(entry)

        self._search_for_matches()

        # print("Match quality scores:")
        # for u1, u2, score in self._match_quality_scores:
        #     print(f"{u1} vs {u2}: {score}")

    def _search_for_matches(self, start_index: int = 0) -> None:
        """
        Updates the matchmaking manager.

        start_index (int, optional): The position in queue to start matching from.
        Used for recursion. Defaults to 0.
        """
        if len(self._queue) < self._min_players_waiting():
            return

        for i in range(start_index, len(self._queue)):
            for j in range(i + 1, len(self._queue)):
                # try to match all players against each other
                if self._try_start_game(self._queue[i], self._queue[j]):
                    # Players are matched and removed from queue. Continue searching.
                    self._search_for_matches(i)
                    return
        return

    def _min_players_waiting(self) -> int:
        """
        Returns the minimum number of players that need to be waiting in the queue.

        Returns:
            int: The minimum number of players.
        """
        return int(
            len(self.player_manager.auth_players) * self._percentage_min_players_waiting
        )

    def _try_start_game(self, player1: QueueEntry, player2: QueueEntry) -> bool:
        """
        Tries to start a game with the given players.

        Args:
            player1: The first player.
            player2: The second player.

        Returns:
            bool: True if the game was started, False otherwise.
        """
        # prevent the user from playing against himself
        if player1.user.user_id == player2.user.user_id:
            return False

        # do not match if both players are bots
        if (
            UserRole(player1.user.role) == UserRole.BOT
            and UserRole(player2.user.role) == UserRole.BOT
        ):
            return False

        match_quality = self._rate_match_quality(player1, player2)
        self._match_quality_scores.append(
            (player1.user.username, player2.user.username, match_quality)
        )

        if match_quality > self._match_quality_threshold:
            # match the players. We could search for best match but using the first adds
            # a bit of diversity and the players in front of the queue are waiting
            # longer, so its fairer for them.

            players = [
                self.player_manager.get_player_by_id(player1.player_id),
                self.player_manager.get_player_by_id(player2.player_id),
            ]

            filtered_players = [player for player in players if player is not None]

            if len(filtered_players) != 2:
                self._log.error("Player was in queue but not in player manager")
                if players[0] is None:
                    self.remove(player1.player_id)
                if players[1] is None:
                    self.remove(player2.player_id)
                return False

            self.remove(player1.player_id)
            self.remove(player2.player_id)

            game = self.game_manager.start_game(filtered_players)
            game.add_finish_callback(self._end_game)
            return True
        return False

    def _rate_match_quality(self, player1: QueueEntry, player2: QueueEntry) -> float:
        """
        Rates the match quality between two players.

        Args:
            player1: The first player.
            player2: The second player.

        Returns:
            float: The match quality.
        """
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
        return draw_prob + waiting_bonus

    def _end_game(self, game: IGame) -> None:
        """
        Readds players to queue after game has ended.

        Args:
            game (IGame): The game to be ended.
        """
        # update elo values
        result = game.get_result()
        if result is not None:
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
