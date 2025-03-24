***************************
How to implement a new game
***************************


Implementing the ``IGame`` Interface
====================================

The Game Class only implements game logic and does not have to handle
networking (e.g. collecting actions, disconnected players), matchmaking
or database tasks. In general, a Game can also implement a game with
more than two players, but the Matchmaking and the Database has to be
updated for this.

Start implementing the interface with

.. code:: python

   from comprl.server.interfaces import IGame, IPlayer

   class MyGame(IGame):
       def __init__(self, players: list[IPlayer]) -> None:
           super().__init__(players)

       ...

and implement all the necessary methods listed below:

-  ``update(actions: dict[PlayerID, list[float]]) -> bool``

   -  Updates the environment
   -  Input: All the collected actions in a dictionary
   -  Returns ``True`` if the game should end ``False`` otherwise

-  ``_validate_action(action: list[float])``

   -  Returns ``True`` if the action is valid
   -  Disconnects the player if the action is invalid which ends the
      game

-  ``_get_observation(id: PlayerID) -> list[float]``

   -  Returns the observation that should be sent to this player
   -  Observations can be sent to each player individually (e.g. for
      left and right players)

-  ``_player_won(id: PlayerID) -> bool``

   -  Returns ``True`` if the player has won, ``False`` otherwise
   -  Should return ``False`` for all players in case of a draw

-  ``_player_stats(id: PlayerID) -> list[float]``

   -  Is called at the end of the game
   -  Can be used to communicate Statistics at the end of the game
   -  e.g. scores, disconnects, rounds, …

For the implementation of these methods the following instance variables
can be helpful:

-  ``self.players: dict[PlayerID, Player]`` a dictionary with all
   players of the game

-  ``self.scores: dict[PlayerID, float]`` a dictionary with all scores
   (defaults to all scores 0.0)


Example: Hockey game
====================

For a real-life example on how to implement a server for a specific game, see the
implementation in ``comprl-hockey-game`` (in the comprl repository).
