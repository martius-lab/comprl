"""State for the protected pages."""

import dataclasses
from typing import Sequence

import reflex as rx
import sqlalchemy as sa

from comprl.server.data.sql_backend import Game, User
from comprl.server.data.interfaces import GameEndState

from . import config, reflex_local_auth
from .reflex_local_auth.local_auth import get_session


@dataclasses.dataclass
class GameStatistics:
    num_games_played: int = 0
    num_games_won: int = 0
    num_disconnects: int = 0


@dataclasses.dataclass
class GameInfo:
    player1: str
    player2: str
    result: str
    time: str
    id: str


class ProtectedState(reflex_local_auth.LocalAuthState):
    def on_load(self):
        if not self.is_authenticated:
            return reflex_local_auth.LoginState.redir


class UserDashboardState(ProtectedState):
    game_statistics: GameStatistics = GameStatistics()

    def on_load(self):
        super().on_load()
        self.game_statistics = self._load_game_statistics()

    def do_logout(self):
        self.game_statistics = GameStatistics()
        return reflex_local_auth.LocalAuthState.do_logout

    def _load_game_statistics(self):
        stats = GameStatistics()

        with get_session() as session:
            stats.num_games_played = (
                session.query(Game)
                .filter(
                    sa.or_(
                        Game.user1 == self.authenticated_user.user_id,
                        Game.user2 == self.authenticated_user.user_id,
                    )
                )
                .with_entities(sa.func.count())
                .scalar()
            )

            stats.num_games_won = (
                session.query(Game)
                .filter(Game.winner == self.authenticated_user.user_id)
                .with_entities(sa.func.count())
                .scalar()
            )

            stats.num_disconnects = (
                session.query(Game)
                .filter(Game.disconnected == self.authenticated_user.user_id)
                .with_entities(sa.func.count())
                .scalar()
            )
        return stats

    def _get_ranked_users(self) -> Sequence[User]:
        with get_session() as session:
            stmt = sa.select(User).order_by((User.mu - User.sigma).desc())
            ranked_users = session.scalars(stmt).all()

        return ranked_users

    @rx.var(cache=True)
    def ranked_users(self) -> Sequence[tuple[int, str, str]]:
        return [
            (i + 1, user.username, f"{user.mu:.2f} / {user.sigma:.2f}")
            for i, user in enumerate(self._get_ranked_users())
        ]

    @rx.var(cache=True)
    def ranking_position(self) -> int:
        if not self.is_authenticated:
            return -1

        for i, user in enumerate(self._get_ranked_users()):
            if user.user_id == self.authenticated_user.user_id:
                return i + 1
        return -1


class UserGamesState(ProtectedState):
    user_games_header: list[str] = ["Player 1", "Player 2", "Result", "Time", "ID", ""]
    user_games: list[GameInfo] = []
    search_id: str = ""

    total_items: int
    offset: int = 0
    limit: int = 10

    def do_logout(self):
        self.user_games = []
        self.search_id = ""
        return reflex_local_auth.LocalAuthState.do_logout

    def _get_num_user_games(self) -> int:
        with get_session() as session:
            return (
                session.query(Game)
                .filter(
                    sa.or_(
                        Game.user1 == self.authenticated_user.user_id,
                        Game.user2 == self.authenticated_user.user_id,
                    )
                )
                .with_entities(sa.func.count())
                .scalar()
            )

    def _get_user_games(self) -> Sequence[Game]:
        if not self.is_authenticated:
            return []

        with get_session() as session:
            stmt = (
                sa.select(Game)
                .options(
                    sa.orm.joinedload(Game.user1_),
                    sa.orm.joinedload(Game.user2_),
                    sa.orm.joinedload(Game.winner_),
                    sa.orm.joinedload(Game.disconnected_),
                )
                .filter(
                    sa.or_(
                        Game.user1 == self.authenticated_user.user_id,
                        Game.user2 == self.authenticated_user.user_id,
                    )
                )
                .order_by(Game.start_time.desc())
                .offset(self.offset)
                .limit(self.limit)
            )
            if self.search_id:
                stmt = stmt.filter(Game.game_id == self.search_id)

            return session.scalars(stmt).all()

    @rx.var(cache=True)
    def page_number(self) -> int:
        return (self.offset // self.limit) + 1 + (1 if self.offset % self.limit else 0)

    @rx.var(cache=True)
    def total_pages(self) -> int:
        return self.total_items // self.limit + (
            1 if self.total_items % self.limit else 0
        )

    @rx.event
    def first_page(self):
        self.offset = 0
        self.load_user_games()

    @rx.event
    def prev_page(self):
        self.offset = max(self.offset - self.limit, 0)
        self.load_user_games()

    @rx.event
    def next_page(self):
        if self.offset + self.limit < self.total_items:
            self.offset += self.limit
        self.load_user_games()

    @rx.event
    def search_game(self, form_data):
        self.offset = 0
        self.search_id = form_data["search_id"]
        self.load_user_games()

    @rx.event
    def clear_search(self):
        self.offset = 0
        self.search_id = ""
        self.load_user_games()

    @rx.event
    def load_user_games(self) -> None:
        self.user_games = []
        for game in self._get_user_games():
            if game.end_state == GameEndState.WIN:
                result = f"{game.winner_.username} won ({game.score1} : {game.score2})"
            elif game.end_state == GameEndState.DRAW:
                result = f"Draw ({game.score1} : {game.score2})"
            elif game.end_state == GameEndState.DISCONNECTED:
                result = f"{game.disconnected_.username} disconnected"
            else:
                result = "Unknown"

            self.user_games.append(
                GameInfo(
                    game.user1_.username,
                    game.user2_.username,
                    result,
                    str(game.start_time.strftime("%Y-%m-%d %H:%M:%S")),
                    str(game.game_id),
                )
            )

        self.total_items = self._get_num_user_games()

    @rx.event
    def download_game(self, game_id: str):
        game_file_name = f"{game_id}.pkl"
        game_file_path = config.get_config().data_dir / "game_actions" / game_file_name

        try:
            data = game_file_path.read_bytes()
        except Exception:
            raise RuntimeError("Game file not found") from None

        return rx.download(filename=game_file_name, data=data)
