***********
Score Decay
***********

If a user is strong in the beginning and plays a lot, they will get a very good score.
If they then stop playing, that good score stays, even if other users maybe got better
in the meantime.  To avoid that, inactiveness is penalised by slowly lowering the score
of inactive users over time.

Score decay is disabled by default but can be enabled in the config file, see :class:`Configuration <comprl.server.config.ScoreDecayConfig>`.

The score decay is applied once every :class:`~comprl.server.config.ScoreDecayConfig.interval_minutes` minutes based on these rules:

- If no games have been played at all in the last interval, nothing happens.
- Otherwise, the :math:`\sigma` rating of all players who didn't participate in at least
  one of these games is increased by
  :class:`~comprl.server.config.ScoreDecayConfig.delta`.
- :math:`\sigma` will not be increased beyond the initial default value.
- The :math:`\mu` rating is not modified by the score decay.
