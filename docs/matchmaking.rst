***********************
Ranking and matchmaking
***********************

Ranking and matchmaking are based on `OpenSkill <openskill.me>`_, using the
`Plackett-Luce Model
<https://openskill.me/en/stable/api/openskill.models.weng_lin.plackett_luce.html>`_


Nomenclature
============

There is an distinction between "user" and "player" which is relevant in some cases.

- User: A registered account.
- Player: A connected client.  A user can connect multiple clients in parallel to
  increase the game throughput.


.. _leaderboard_ranking:

Leaderboard Ranking
===================

Each user has a score which consists of a values :math:`\mu` and :math:`\sigma`.
:math:`\mu` represents the skill of the user, and :math:`\sigma` the uncertainty of that
skill value.  After each game, these values are updated based on the outcome of the game
(won, lost, draw).

For the leaderboard, the users are than ranked based on :math:`\mu - \sigma`.

.. note::

   The default in OpenSkill is actually :math:`\mu - 3\sigma`.  We should investigate,
   if we want to use that as well.


Matchmaking
===========

In previous versions the draw probability based on the Plackett-Luce model was used to
determine match quality for pairs of players in the queue.  This resulted in some top
players having very low match quality with literally everyone else, as their scores
where too different.  Therefore, the current version uses a custom "Gauss-Leaderboard",
see below for more information.

When clients connect to the server, they are added to the queue of waiting players.
Every few seconds, the server tries to find good matches for the players in the queue.
Starting with the first player, a match quality score is computed for each other player
in the queue.  All pairs with a score below
:attr:`comprl.server.config.Config.match_quality_threshold` are discarded.  From the
rest, one is randomly sampled using the score as weight.


Minimum waiting players
-----------------------

Matchmaking only happens if the number of layers in the queue is higher or equal to

::

    num_connected_players * percentage_min_players_waiting

See :attr:`comprl.server.config.Config.percentage_min_players_waiting`.


Match Quality Score
-------------------

The match quality score of a pair of players is the sum of two components:

- Gauss-Leaderboard score
- Waiting time bonus

Gauss-Leaderboard Score
^^^^^^^^^^^^^^^^^^^^^^^

The Gauss-Leaderboard score uses the leaderboard ranking based on the OpenSkill rating
(see :ref:`leaderboard_ranking`) and computes the match quality of two users with a
Gauss function over the distance of these users in the leaderboard.
The standard deviation of this Gauss function can be configured with the parameter
:attr:`comprl.server.config.Config.gauss_leaderboard_rater_sigma`.

This score has the advantage, that for each user there is always a number of other
users, which are considered good matches, independent of the actual user ratings.  The
ratings only affect *which* players will have high match scores.  This avoids an issue
in previous versions (where OpenSkill's draw probability was used instead), where some
top users were so far above the rest, that they didn't get a good match score for any
other user anymore.


Waiting Time Bonus
^^^^^^^^^^^^^^^^^^

To prevent players without a good match from waiting in the queue forever, they get a
waiting bonus, that increases over time as they wait in the queue.  So independent of
their skill, the overall score will at some point be high enough that they find a match.

The time bonus is computed as a fraction of the combined waiting time of the two players
in minutes.  It only starts after one minute of combined waiting.  It can be scaled with
the configuration parameter :attr:`~comprl.server.config.Config.percental_time_bonus`.
