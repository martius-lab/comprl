import pytest
from sqlalchemy.exc import IntegrityError

from comprl.server.util import IDGenerator
from comprl.server.data.interfaces import GameEndState, GameResult
from comprl.server.data import ConnectionInfo, GameData
from comprl.server.data.sql_backend import create_database_tables


def test_game_data(tmp_path):
    db_file = tmp_path / "database.db"
    create_database_tables(db_file)

    table_name = "games"
    game_data = GameData(ConnectionInfo(host=db_file, table=table_name))

    # add some test games
    game1_uuid = IDGenerator.generate_game_id()
    game2_uuid = IDGenerator.generate_game_id()
    game3_uuid = IDGenerator.generate_game_id()
    game4_uuid = IDGenerator.generate_game_id()
    game_data.add(
        GameResult(
            game_id=game1_uuid,
            user1_id=1,
            user2_id=2,
            score_user_1=3,
            score_user_2=6,
        )
    )
    game_data.add(
        GameResult(
            game_id=game2_uuid,
            user1_id=1,
            user2_id=2,
            score_user_1=3,
            score_user_2=6,
            start_time="2021-01-01 12:00:00",
            end_state=GameEndState.DRAW,
        )
    )
    game_data.add(
        GameResult(
            game_id=game3_uuid,
            user1_id=1,
            user2_id=2,
            score_user_1=3,
            score_user_2=6,
            start_time="2021-01-01 13:00:00",
            end_state=GameEndState.WIN,
            is_user1_winner=True,
        )
    )
    game_data.add(
        GameResult(
            game_id=game4_uuid,
            user1_id=1,
            user2_id=2,
            score_user_1=3,
            score_user_2=6,
            start_time="2021-01-01 13:00:00",
            end_state=GameEndState.DISCONNECTED,
            is_user1_disconnected=True,
        )
    )

    # check that I can't add two games with same ID
    with pytest.raises(IntegrityError):
        game_data.add(
            GameResult(
                game_id=game1_uuid,
                user1_id=1,
                user2_id=2,
                score_user_1=3,
                score_user_2=6,
            )
        )

    assert len(game_data.get_all()) == 4

    # TODO check the data returned by get_all
