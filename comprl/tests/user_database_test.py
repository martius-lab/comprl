import pytest

from comprl.server.data import User, UserData, get_session, init_engine
from comprl.server.data.models import create_database_tables


def set_matchmaking_parameters(user_id: int, mu: float, sigma: float) -> None:
    """
    Sets the matchmaking parameters of a user based on their ID.

    Args:
        user_id (int): The ID of the user.
        mu (float): The new mu value of the user.
        sigma (float): The new sigma value of the user.
    """
    with get_session() as session:
        user = session.get(User, user_id)
        if user is None:
            raise ValueError(f"User with ID {user_id} not found.")

        user.mu = mu
        user.sigma = sigma
        session.commit()


def test_user_data(tmp_path):
    db_file = tmp_path / "database.db"
    create_database_tables(db_file)
    init_engine(db_file)

    # add test users to database and collect IDs
    users = [("player_1", "token1"), ("player_2", "token2"), ("player_3", "token3")]
    user_ids = [
        UserData.add(user_name=u[0], user_password="pass", user_token=u[1])
        for u in users
    ]

    for user_id, user in zip(user_ids, users, strict=True):
        _user = UserData.get_user_by_token(user[1])
        assert _user is not None
        assert _user.user_id == user_id
        assert _user.username == user[0]

    set_matchmaking_parameters(user_id=user_ids[1], mu=23.0, sigma=3.0)
    mu0, sigma0 = UserData.get_rating(user_ids[0])
    mu1, sigma1 = UserData.get_rating(user_ids[1])

    # user0 was unmodified, so here the default values should be returned
    assert pytest.approx(mu0) == 25.0
    assert pytest.approx(sigma0) == 8.333

    # user1 was updated above
    assert pytest.approx(mu1) == 23.0
    assert pytest.approx(sigma1) == 3.0
