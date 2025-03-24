***********
Admin Tools
***********

CompRL ships with a bunch of tools for maintenance and monitoring of the system.  Below
is only a high level overview of what they do.  Run each of them with ``--help`` to get
a complete list of options.


comprl-games
============

Takes a config file or database as argument and prints a list of all played games.


comprl-users
============

List, show, add and edit users (e.g. to change a password or turn a normal user into a
bot).


comprl-monitor
==============

Shows live information about connected players, running games and the waiting queue.

Usage: ``comprl-monitor [<path-to-monitor-file>]``

The monitor file is written and updated by the server after each round of matchmaking.
If not specified, it is expected to be at its default location
``/dev/shm/comprl_monitor``.


comprl-score-decay
==================

Slowly increase the sigma rating of users over time.

Periodically increase the sigma rating of all users by a fixed amount.  This is to
penalize users who have not played in a while. Otherwise a user with a good start could
just stop after few games and keep a good score, while other users might be better in
the meantime. Increasing sigma of everyone by a fixed amount does not change the ranking
(it might affect matchmaking, though?). Only users who don't play anymore will slowly
move down in the ranking.


create_database.py
==================

Create/initialize a new database.

Usage: ``python -m comprl.scripts.create_database ...``


dummy_user.py
=============

Create four dummy users "test1" to "test4" with passwords "password1", ... and access
tokens "token1", ...

Usage: ``python -m comprl.scripts.dummy_user ...``
