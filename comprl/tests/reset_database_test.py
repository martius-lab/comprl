import pytest

from comprl.server.data import UserData, GameData
from comprl.server.util import IDGenerator
from comprl.server.data.interfaces import GameEndState, GameResult
from comprl.server.data.models import create_database_tables
import comprl.scripts.reset as reset


def test_reset(tmp_path):
    db_path = tmp_path / "database.db"
    create_database_tables(db_path)

    user_data = UserData(db_path)
    game_data = GameData(db_path)

    # add test data

    userID1 = user_data.add(
        user_name="user_1",
        user_password="pw1",
        user_token=str(IDGenerator.generate_player_id()),
    )
    userID2 = user_data.add(
        user_name="user_2",
        user_password="pw2",
        user_token=str(IDGenerator.generate_player_id()),
    )
    userID3 = user_data.add(
        user_name="user_3",
        user_password="pw3",
        user_token=str(IDGenerator.generate_player_id()),
    )
    userID4 = user_data.add(
        user_name="user_4",
        user_password="pw4",
        user_token=str(IDGenerator.generate_player_id()),
    )

    user_data.set_matchmaking_parameters(user_id=userID1, mu=24.000, sigma=9.333)
    user_data.set_matchmaking_parameters(user_id=userID2, mu=23.000, sigma=9.000)
    user_data.set_matchmaking_parameters(user_id=userID3, mu=22.000, sigma=7.000)
    user_data.set_matchmaking_parameters(user_id=userID4, mu=21.000, sigma=7.333)

    gameID1, gameID2, gameID3 = (
        IDGenerator.generate_game_id(),
        IDGenerator.generate_game_id(),
        IDGenerator.generate_game_id(),
    )
    game1 = GameResult(
        game_id=gameID1, user1_id=23, user2_id=4, score_user_1=3, score_user_2=6
    )
    game2 = GameResult(
        game_id=gameID2, user1_id=43, user2_id=23, score_user_1=6, score_user_2=7
    )
    game3 = GameResult(
        game_id=gameID3,
        user1_id=1,
        user2_id=23,
        score_user_1=6,
        score_user_2=7,
        end_state=GameEndState.DISCONNECTED.value,
    )
    game_data.add(game_result=game1)
    game_data.add(game_result=game2)
    game_data.add(game_result=game3)

    assert len(game_data.get_all()) == 3

    # reset
    reset.reset_games(game_data=game_data)
    reset.reset_elo(user_data=user_data)

    # test
    for user_id in (userID1, userID2, userID3, userID4):
        mu, sigma = user_data.get_matchmaking_parameters(user_id=user_id)
        assert pytest.approx(mu) == 25.0, f"user_id: {user_id}"
        assert pytest.approx(sigma) == 8.333, f"user_id: {user_id}"

    assert len(game_data.get_all()) == 0
