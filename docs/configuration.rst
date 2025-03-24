*************
Configuration
*************

The server is configured through a TOML file.  For available options see
:class:`comprl.server.config.Config` below.  Entries in the config file should have same
name as the Config class attributes.  Default value "???" means that the parameter is
required.  For all others the corresponding default value is used if not set.

.. autoclass:: comprl.server.config.Config
   :members:


Example
-------

.. literalinclude:: ../comprl-hockey-game/config.toml
