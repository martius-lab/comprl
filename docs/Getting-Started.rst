***************
Getting Started
***************


Server
======

To host your competition, implement a new game by inheriting from the ``IGame``
interface provided by the ``comprl.server.interfaces`` module (see
:doc:`/implementing_a_game`).

Once your game is fully implemented, use a configuration file or command-line
arguments to start the server with the desired configuration (for more see
:doc:`/configuration`).

.. code:: sh

   #display all possible command line arguments
   python -m comprl.server -h

   #run the server by providing a config file
   python -m comprl.server --config="path/to/config.toml"


Client
======

See :doc:`/how_to_implement_client`.


.. _examples:

Examples
========

Simple
------

This example can be found in
```comprl/examples/simple`` <https://github.com/martius-lab/teamproject-competition-server/tree/main/examples/simple>`__.

The game logic is very simple: The two agents send integers, these are
added up, when the sum reaches 10 the game ends. The sent integers can
be manually entered in the console. This game is supposed to
demonstrates the basics of a game and can be used for easy testing.

.. code:: sh

   #run game by providing a config file
   python -m comprl.server --config="examples/simple/config.toml"

   #run agent
   python -m examples.simple.agent

Rock-Paper-Scissors
-------------------

This example can be found in ```comprl/examples/rockpaperscissors``
<https://github.com/martius-lab/teamproject-competition-server/tree/main/examples/rockpaperscissors>`__.

In this game the two agents play rock-paper-scissors until one of them has won three
times. The agent sent random actions.

.. code:: sh

   #run game by providing a config file
   python -m comprl.server --config="examples/rockpaperscissors/config.toml"

   #run agent
   python -m examples.rockpaperscissors.agent

Hockey
------

This example can be found in ```comprl-hockey-game``
<https://github.com/martius-lab/teamproject-competition-server/tree/main/comprl-hockey-game>`__.

Two agents play several rounds of the `hockey game
<https://github.com/martius-lab/hockey-env/>`__. After each round sides are swapped.

.. code:: sh

   #run game by providing a config file
   python -m comprl.server --config="examples/hockey/config.toml"

   #run one of the following agents
   python -m examples.hockey.weak_hockey_agent
   python -m examples.hockey.strong_hockey_agent
   python -m examples.hockey.random_hockey_agent
