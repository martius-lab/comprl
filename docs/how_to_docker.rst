**************************************************
How to run the server + web interface using Docker
**************************************************

The CompRL repository contains an implementation of a simply "hockey" game, included in the ``comprl-hockey-game`` folder.  This also contains a Docker compose config for running the game server in a container.
Further, the ``comprl-web-reflex`` folder contains Docker compose files for running the web interface in containers.

**Note:** Currently the Docker setup for the web interface has some paths hard-coded for the hockey game, so when used for another game, the compose.yaml needs to be adjusted.

Some manual setup is needed to get things running:

1. Clone the comprl repo
2. Create a data folder somewhere and set ``o+w`` permission.
   Initialise the database file with name ``hockey.db`` in that folder (TODO: add
   instructions for this)
3. Create a file ``.env`` somewhere with the following content:

   .. code:: sh

      COMPRL_DATA_PATH="<path to the data folder created in the previous step>"
      DOMAIN=your.server-domain.com

   Create symlinks to that file in both ``comprl-hockey-game`` and ``comprl-web-reflex``.
4. Make sure the directory specified above exists and has ``o+w`` permissions.
5. Adjust configuration to your needs in ``comprl-hockey-game/config-docker.toml``
   (note that paths to database and data directory refer to inside the container and
   should be kept at ``/comprl-data``).
   You can also put the config file somewhere else and specify the path by adding
   the following to the ``.env`` file:

   .. code:: sh

      COMPRL_CONFIG_PATH="/path/to/config.toml"

6. Start the game server by running

   .. code:: sh

      sudo make up-server

   in ``comprl-hockey-game``
7. Start the web server by running

   .. code:: sh

      sudo make up

   in ``comprl-web-reflex``

Both can be stopped again by running ``sudo make down`` in both directories.


Run Bots
========

Create two bot users and add their access tokens in the ``.env`` file:

.. code:: sh

    STRONG_BOT_ACCESS_TOKEN=token2
    WEAK_BOT_ACCESS_TOKEN=token1

Launch be bots with

.. code:: sh

   sudo make up-bots

in ``comprl-hockey-game``.

To stop only the bots but keep the server running, you can use

.. code:: sh

   sudo make stop-bots


Reloading Configuration
=======================

The game server can reload some of the config parameters by sending a SIGHUP signal (see
:ref:`reload_config`).  To make this easy, the Makefile in ``comprl-hockey-game`` contains
a "reload" target, so the reload can be triggered with

.. code:: sh

   sudo make reload
