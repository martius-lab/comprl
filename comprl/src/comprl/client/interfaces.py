"""This module contains the interface for the agent."""

import abc


class IAgent(abc.ABC):
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

        The default implementation always returns True.
        May be overridden to implement some method of non-disruptive disconnection (e.g.
        stop after 10 games).

        Returns:
            bool: True if the agent is ready to play, False otherwise.
        """
        return True

    def on_start_game(self, game_id: int) -> None:  # noqa: B027
        """
        Called when a new game starts.

        The default implementation does nothing.  Override to implement custom behavior.

        Args:
            game_id (int): The ID of the new game.
        """
        pass

    @abc.abstractmethod
    def get_step(self, obv: list[float]) -> list[float]:
        """
        Requests the agent's action based on the current observation.

        Args:
            obv (list[float]): The current observation.

        Returns:
            list[float]: The agent's action.
        """
        raise NotImplementedError("step function not implemented")

    def on_end_game(self, result: bool, stats: list[float]) -> None:  # noqa: B027
        """
        Called when a game ends.

        The default implementation does nothing.  Override to implement custom behavior.

        Args:
            result: The result of the game (True if won, False if lost or draw).
            stats: The statistics of the game.  The meaning of the values depends on the
                game implementation.
        """
        pass

    def on_error(self, msg: str):  # noqa: B027
        """
        Called when an error occurs.

        Args:
            msg (str): The error message.
        """
        pass

    def on_message(self, msg: str):  # noqa: B027
        """Called when a message is sent from the server.

        Args:
            msg (str): The message
        """
        pass

    def on_disconnect(self):  # noqa: B027
        """Called when the agent disconnects from the server."""
        pass
