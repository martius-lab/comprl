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
:ref:`server_config`).

.. code:: sh

   #display all possible command line arguments
   python -m comprl.server --h

   #run the server by providing a config file
   python -m comprl.server --config="path/to/config.toml"

.. _server_config:

Config File
-----------

The server is configured through a TOML file.  For available options see
:class:`comprl.server.config.Config` below.  Entries in the config file should have same
name as the Config class attributes.  Default value "???" means that the parameter is
required.  For all others the corresponding default value is used if not set.

.. autoclass:: comprl.server.config.Config
   :members:

For examples of a config file see :ref:`examples`.


Stored game actions
-------------------

.. todo:: needs update

The actions of each game are stored in a python dictionary and this
dictionary is stored in a file using the `pickle
library <https://docs.python.org/3/library/pickle.html>`__. The actions
can be retrieved with the key ``""actions""``.

Additionally, the files of hockey games support the following keys: -
``num_rounds``: number of rounds played - ``actions_round_0``: actions
of the first round - ``actions_round_1``: actions of the second round -
… - ``actions_round_(num_rounds-1)``: actions of the last round -
``observations_round_0``: observations of the first round - …


Scripts
-------

.. todo:: needs update

The following three scripts can be helpful to handle the user database.

.. code:: sh

   #script to add dummy user to the user database
   python -m comprl.scripts.dummy_user

   #script to add new user to the user database
   python -m comprl.scripts.new_user

   #script to reset the game database and the mu and sigma in the user database
   python -m comprl.scripts.reset

The database information can be given by line parameter or by the same
config file that is used for the server. For example:

::

   python -m comprl.scripts.dummy_user --config="examples/hockey/config.toml"


Client
======

See :doc:`/how_to_implement_client`.



.. _examples:


Examples
========

.. todo:: probably needs to be updated

Simple
------

This example can be found in
```\examples\simple`` <https://github.com/martius-lab/teamproject-competition-server/tree/main/examples/simple>`__.

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

This example can be found in
```examples/rockpaperscissors`` <https://github.com/martius-lab/teamproject-competition-server/tree/main/examples/rockpaperscissors>`__.

In this game the two agents play rock-paper-scissors until one of them
has won three times. The agent sent random actions.

.. code:: sh

   #run game by providing a config file
   python -m comprl.server --config="examples/rockpaperscissors/config.toml"

   #run agent
   python -m examples.rockpaperscissors.agent

Hockey
------

This example can be found in
```examples/hockey`` <https://github.com/martius-lab/teamproject-competition-server/tree/main/examples/hockey>`__.

Two agents play several rounds of the `hockey
game <https://github.com/martius-lab/laser-hockey-env/>`__. After each
round sides are swapped.

.. code:: sh

   #run game by providing a config file
   python -m comprl.server --config="examples/hockey/config.toml"

   #run one of the following agents
   python -m examples.hockey.weak_hockey_agent
   python -m examples.hockey.strong_hockey_agent
   python -m examples.hockey.random_hockey_agent
