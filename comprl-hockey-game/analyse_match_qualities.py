#!/usr/bin/env python
# coding: utf-8

# In[ ]:

import argparse
import datetime

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import sqlalchemy as sa

from comprl.server.data.sql_backend import (
    User,
    init_engine,
    get_session,
)
from comprl.server.managers import GaussLeaderboardRater, QueueEntry


def main():
    parser = argparse.ArgumentParser(
        description="Analyse match qualities of the GaussLeaderboardRater on the hockey dataset."
    )
    parser.add_argument(
        "database_path",
        type=str,
        help="Path to the SQLite database containing the hockey game data.",
    )
    args = parser.parse_args()

    init_engine(args.database_path)

    with get_session() as session:
        stmt = sa.select(User)
        users = {u.user_id: u for u in session.execute(stmt).scalars()}

    glr = GaussLeaderboardRater(sigma_func=lambda: 30.0)
    glr.update_model()
    n_users = len(glr.ranked_users)

    # match quality comparision

    match_qualities = np.zeros((n_users, n_users))
    for i1, user_id1 in enumerate(glr.ranked_users):
        user1 = QueueEntry(
            player_id="foo",
            user=users[user_id1],
            in_queue_since=datetime.datetime.now(),
        )
        for i2, user_id2 in enumerate(glr.ranked_users):
            user2 = QueueEntry(
                player_id="foo",
                user=users[user_id2],
                in_queue_since=datetime.datetime.now(),
            )
            match_qualities[i1, i2] = glr.rate(user1, user2)

    fig, ax = plt.subplots(1, 1, figsize=(8, 7))
    sns.heatmap(
        match_qualities,
        yticklabels=[users[uid].username for uid in glr.ranked_users],
        xticklabels=[users[uid].username for uid in glr.ranked_users],
        cmap="inferno",
        ax=ax,
    )
    ax.set_title("Match qualities")
    outpath = "/tmp/match_qualities.png"
    print(f"Saving match quality heatmap to {outpath}")
    fig.savefig(outpath, dpi=200, bbox_inches="tight")
    plt.show()


if __name__ == "__main__":
    main()
