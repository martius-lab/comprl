from comprl.server.interfaces import IGame, IPlayer
from comprl.shared.types import PlayerID

import hockey.hockey_env as h_env
import numpy as np
from typing import List


class HockeyGame(IGame):
    """game class with the game logic being the laser-hockey env"""

    def __init__(self, players: list[IPlayer]) -> None:
        """create a game

        Args:
            players (list[IPlayer]): list of players participating in this game.
                                      Handled by the abstract class
        """

        self.env = h_env.HockeyEnv()
        self.player_1_id = players[0].id
        self.player_2_id = players[1].id

        # number of rounds played per game
        self.num_rounds: int = 4
        self.remaining_rounds = self.num_rounds
        # Bool weather players play in default orientation or sides are swapped.
        # Alternates between rounds.
        self.sides_swapped = False
        # Bool if all rounds are finished
        self.finished = False

        # initialize terminated and truncated, so the game hasn't ended by default.
        self.terminated = False
        self.truncated = False

        # array storing all actions/observations of a round to be saved later.
        # contains tuples consisting of the actions of the players
        # (in the order of the player dictionary)
        self.actions_this_round: List[np.ndarray] = []
        self.observations_this_round: List[np.ndarray] = []

        # self.game_info also contains:
        # - num_rounds: number of rounds played
        # - actions_round_0: actions of the first round
        # - actions_round_1: actions of the second round
        # - ...
        # - actions_round_(num_rounds-1): actions of the last round
        # - observations_round_0: observations of the first round
        # - ...

        super().__init__(players)

    def start(self):
        """
        notifies all players that the game has started
        and starts the game cycle
        """

        self.obs_player_one, self.info = self.env.reset()
        self.observations_this_round.append(self.obs_player_one)
        return super().start()

    def _end(self, reason="unknown"):
        """notifies all players that the game has ended

        Args:
            reason (str, optional): reason why the game has ended.
                                    Defaults to "unknown"
        """
        self.env.close()
        # add useful information to the game_info
        self.game_info["num_rounds"] = [
            np.array([self.num_rounds])
        ]  # to respect type of dict
        return super()._end(reason)

    def _update(self, actions_dict: dict[PlayerID, list[float]]) -> bool:
        """perform one gym step, using the actions

        Returns:
            bool: True if the game is over, False otherwise.
        """
        # self.env.render(mode="human")  # (un)comment to render or not

        self.action = np.hstack(
            [
                actions_dict[self.player_1_id],
                actions_dict[self.player_2_id],
            ]
        )
        (
            self.obs_player_one,
            self.reward,
            self.terminated,
            self.truncated,
            self.info,
        ) = self.env.step(self.action)

        # store the actions and observations
        self.actions_this_round.append(self.action)
        self.observations_this_round.append(self.obs_player_one)

        # check if current round has ended
        if self.terminated or self.truncated:
            # update score
            self.winner = self.info["winner"]
            if self.winner == 1:
                self.scores[self.player_1_id] += 1
            if self.winner == -1:
                self.scores[self.player_2_id] += 1

            # store the actions and observations of the round
            self.game_info[
                "actions_round_" + str(self.num_rounds - self.remaining_rounds)
            ] = self.actions_this_round
            self.actions_this_round = []
            self.game_info[
                "observations_round_" + str(self.num_rounds - self.remaining_rounds)
            ] = self.observations_this_round
            self.observations_this_round = []

            # reset env
            self.obs_player_one, self.info = self.env.reset()
            self.observations_this_round.append(self.obs_player_one)
            # DISABLED: swap player side, swap player ids
            # Did not seem to be implemented correctly, was it? The game swaps sides that start anyway.
            # self.sides_swapped = not self.sides_swapped
            # self.player_1_id, self.player_2_id = self.player_2_id, self.player_1_id

            # decrease remaining rounds
            self.remaining_rounds = self.remaining_rounds - 1

            # check if it was the last round
            if self.remaining_rounds == 0:
                self.finished = True

        return self.finished

    def _validate_action(self, action) -> bool:
        """check if the action is in the action space of the env"""
        # can't use self.env.action_space.contains as tis is a action of one player
        # and the action space is for both players. So I basically copied the code from
        # the contains() function.
        action = np.array(action)
        return bool(
            action.shape == (4,) and np.all(action >= -1) and np.all(action <= 1)
        )
        # check if the action is in the action space and thus valid

    def _get_observation(self, id: PlayerID) -> list[float]:
        """return the correct obs respecting if sides are swapped

        Args: id: PlayerID of the player to get the observation for

        Returns: list[float]: observation of the player with the given id"""
        if id == self.player_1_id:
            return self.obs_player_one.tolist()  # obs is an np array, we need list
        else:
            return self.env.obs_agent_two().tolist()  # obs is an np array, we need list

    def _player_won(self, id: PlayerID) -> bool:
        """check if a player has won the game

        Args: id: PlayerID of the player to check

        Returns: bool: True if the player has won, False otherwise"""
        if not self.finished:  # if game hasn't ended nobody has won
            return False

        # determine winner using score
        if id == self.player_1_id:
            return self.scores[self.player_1_id] > self.scores[self.player_2_id]
        if id == self.player_2_id:
            return self.scores[self.player_2_id] > self.scores[self.player_1_id]
        return False

    def _player_stats(self, id: PlayerID) -> list[float]:
        """gets a list of the scores of this player and the other player
        Args: id: PlayerID of the player to get the score of
        Returns: int: score of the player with the given id"""
        other_id = self.player_1_id if self.player_1_id != id else self.player_2_id
        return [self.scores[id], self.scores[other_id]]
