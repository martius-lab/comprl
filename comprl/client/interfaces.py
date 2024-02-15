"""
This module contains the interface for the agent.
"""


class IAgent:
    """agent interface which could be used by the end-user"""

    def run(self, token: str):
        """
        Runs the agent with the specified token.

        Args:
            token (str): The token used for authentication.
        """
        self.token = token

    def auth(self) -> str:
        """
        Returns the authentication token.

        Returns:
            str: The authentication token.
        """
        return self.token

    def is_ready(self) -> bool:
        """
        Returns if the agent is ready to play.

        Returns:
            bool: True if the agent is ready to play, False otherwise.
        """
        return True

    def on_start_game(self, game_id: int) -> None:
        """
        Called when a new game starts.

        Args:
            game_id (int): The ID of the new game.

        Returns:
            bool: True if the agent is ready to play, False otherwise.
        """
        pass

    def get_step(self, obv: list[float]) -> list[float]:
        """
        Requests the agent's action based on the current observation.

        Args:
            obv (list[float]): The current observation.

        Returns:
            list[float]: The agent's action.
        """
        raise NotImplementedError("step function not implemented")

    def on_end_game(self, result, stats) -> None:
        """
        Called when a game ends.

        Args:
            result: The result of the game.
            stats: The statistics of the game.

        Returns:
            bool: True if the agent handled the end of the game, False otherwise.
        """
        pass

    def on_error(self, msg):
        """
        Called when an error occurs.

        Args:
            msg: The error message.
        """
        pass
