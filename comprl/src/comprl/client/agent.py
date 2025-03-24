"""
This module contains the Agent class, used by the end-user connecting to the server.
"""

from typing import final


from comprl.client.interfaces import IAgent
from comprl.client import networking


class Agent(IAgent):
    """Agent used by the end-user connecting to the server.

    This class represents an agent that interacts with the server. It provides methods
    for registering event handlers and connecting to the server.
    """

    def __init__(self) -> None:
        super().__init__()

    @final
    def run(self, token: str, host: str = "localhost", port: int = 65335) -> None:
        """Connects the client to the server.

        This method connects the client to the server using the specified token, host,
        and port. It internally calls the `run` method of the base class to establish
        the connection.

        Args:
            token (str): The token used for authentication.
            host (str): The host address of the server. Defaults to "localhost".
            port (int): The port number of the server. Defaults to 65335.

        Returns:
            None

        """
        super().run(token)
        networking.connect_agent(self, host, port)

    def on_error(self, msg: str):
        """Called if an error occurred on the server side.

        Prints the message to stdout.  May be overridden to implement custom error
        handling.
        """
        print(f"Error: {msg}")

    def on_message(self, msg: str):
        """Called if a message is sent from the server.

        Prints the message to stdout.  May be overridden to implement custom message
        handling.
        """
        print(f"Info: {msg}")

    def on_disconnect(self):
        """Called when the agent disconnects from the server.

        Prints an error message to stdout.  May be overridden to implement custom
        disconnect handling.
        """
        print("Error: Agent disconnected from the server.")
