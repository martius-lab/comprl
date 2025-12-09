import pytest

from comprl.server.data import UserData, init_engine
from comprl.server.data.models import create_database_tables


def test_user_data(tmp_path):
    db_file = tmp_path / "database.db"
    create_database_tables(db_file)
    init_engine(db_file)
    user_data = UserData()

    # add test users to database and collect IDs
    users = [("player_1", "token1"), ("player_2", "token2"), ("player_3", "token3")]
    user_ids = [
        user_data.add(user_name=u[0], user_password="pass", user_token=u[1])
        for u in users
    ]

    for user_id, user in zip(user_ids, users, strict=True):
        _user = user_data.get_user_by_token(user[1])
        assert _user is not None
        assert _user.user_id == user_id
        assert _user.username == user[0]

    user_data.set_matchmaking_parameters(user_id=user_ids[1], mu=23.0, sigma=3.0)
    mu0, sigma0 = user_data.get_matchmaking_parameters(user_ids[0])
    mu1, sigma1 = user_data.get_matchmaking_parameters(user_ids[1])

    # user0 was unmodified, so here the default values should be returned
    assert pytest.approx(mu0) == 25.0
    assert pytest.approx(sigma0) == 8.333

    # user1 was updated above
    assert pytest.approx(mu1) == 23.0
    assert pytest.approx(sigma1) == 3.0
