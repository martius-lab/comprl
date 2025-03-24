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

- :meth:`~comprl.server.interfaces.IGame._update`

  - Updates the environment
  - Input: All the collected actions in a dictionary
  - Returns ``True`` if the game should end ``False`` otherwise

- :meth:`~comprl.server.interfaces.IGame._validate_action`

  - Returns ``True`` if the action is valid
  - Disconnects the player if the action is invalid which ends the game

- :meth:`~comprl.server.interfaces.IGame._get_observation`

  - Returns the observation that should be sent to this player
  - Observations can be sent to each player individually (e.g. for left and right
    players)

- :meth:`~comprl.server.interfaces.IGame._player_won`

  - Returns ``True`` if the player has won, ``False`` otherwise
  - Should return ``False`` for all players in case of a draw

- :meth:`~comprl.server.interfaces.IGame._player_stats`

  - Is called at the end of the game
  - Can be used to communicate Statistics at the end of the game
  - e.g. scores, disconnects, rounds, …

For the implementation of these methods the following instance variables
can be helpful:

-  :attr:`~comprl.server.interfaces.IGame.players`: a dictionary with all
   players of the game

-  :attr:`~comprl.server.interfaces.IGame.scores`: a dictionary with all scores
   (defaults to all scores 0.0)


Stored game actions
===================

The game implementation can store arbitrary information about the game in the dictionary
:attr:`comprl.server.interfaces.IGame.game_info`.  This dictionary is automatically
saved to a pickle file at the end of the game.  The file is written to
``{data_dir}/game_actions/{game_id}.pkl`` (see
:attr:`comprl.server.config.Config.data_dir`).


Example: Hockey game
====================

For a real-life example on how to implement a server for a specific game, see the
implementation in ``comprl-hockey-game`` (in the comprl repository).



API
=== 

.. autoclass:: comprl.server.interfaces.IGame
   :members:
   :private-members:

.. autoclass:: comprl.server.interfaces.IPlayer
   :members:
