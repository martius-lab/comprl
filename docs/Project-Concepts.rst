****************
Project Concepts
****************


IDs
===

This Project has 3 types of IDs: 

User-ID (int)
-------------

- Primary Key for the User database
- is linked to the matchmaking parameters and elo

Player-ID (UUID)
----------------

- Is used to handle and identify clients internally
- Only used during runtime
- There can be different players with the same User-ID

Game-ID (UUID)
--------------

- Is used to identify the game during runtime
- Is used as a primary key in the game database
- files name of the game files with all actions

Password/Token
==============

Username and Password
---------------------

- Used for login to the website.
- Can be freely chosen during registration.
- Username is used for leaderboard.


Token
-----

- Used for authentication when connecting an agent to the server.
- Unique for every user (automatically generated).
- Users can see their access token when logging in to the web interface.


Network Communication
=====================

Network communication between server and clients is done using the `twisted library
<https://twisted.org>`_.

AMP Protocol - shared/commands
------------------------------

.. image:: images/protocol_overview.png
   :alt: Diagram showing the communication protocol between Server and Client.


Database
========

Information about users and played games are stored in a database.

UserData
--------

.. autoclass:: comprl.server.data.sql_backend.User
    :members:
    :undoc-members:


GameData
--------

.. autoclass:: comprl.server.data.sql_backend.Game
    :members:
    :undoc-members:


Matchmaking
===========

See :doc:`matchmaking`.
