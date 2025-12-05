*************
Configuration
*************

The server is configured through a TOML file.  For available options see
:class:`comprl.server.config.Config` below.  Entries in the config file should have same
name as the Config class attributes.  Default value "???" means that the parameter is
required.  For all others the corresponding default value is used if not set.

.. autoclass:: comprl.server.config.Config
   :members:

.. autoclass:: comprl.server.config.MatchmakingConfig
   :members:

.. autoclass:: comprl.server.config.ScoreDecayConfig
   :members:


Example
=======

.. literalinclude:: ../comprl-hockey-game/config.toml


.. _reload_config:

Reload Configuration
====================

Parameters of the ``[comprl.matchmaking]`` and ``[comprl.score_decay]`` sections can be
changed during run time by changing the value in the config file and then sending a
SIGHUP signal to the ``comprl-server`` process to trigger a config reload.

**Important:**

- Only parameters of the ``[comprl.matchmaking]`` and ``[comprl.score_decay]`` sections
  will be reloaded.  Changes to other parts of the config file will only take effect
  after restarting the server.
- If some of the affected settings have been set via the command line, using
  ``--config-overwrites`` when starting the server, those settings will be lost and
  replaced by the values from the config file.  So hot-reloading and
  ``--config-overwrites`` should not be combined!
