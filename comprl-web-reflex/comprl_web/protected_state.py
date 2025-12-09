"""State for the protected pages."""

import dataclasses
import textwrap
import pathlib
from typing import Sequence

import reflex as rx
import sqlalchemy as sa

from comprl.server.data.sql_backend import Game, User, get_ranked_users, hash_password
from comprl.server.data.interfaces import GameEndState

from . import config, reflex_local_auth
from .reflex_local_auth.local_auth import get_session
from .reflex_local_auth.registration import PASSWORD_MIN_LENGTH, validate_username
from .reflex_local_auth.login import verify_password


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
    has_game_file: bool


class ProtectedState(reflex_local_auth.LocalAuthState):
    """Base for protected states."""

    def on_load(self):
        if not self.is_authenticated:
            return reflex_local_auth.LoginState.redir


class UserDashboardState(ProtectedState):
    game_statistics: GameStatistics = GameStatistics()
    ranked_users: list[User] = []

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

    @rx.var(cache=False, initial_value=0)
    def ranking_position(self) -> int:
        if not self.is_authenticated:
            return -1

        with get_session() as session:
            ranked_users_query = session.query(
                User,
                sa.func.rank()
                .over(order_by=User.ranking_order_expression().desc())
                .label("rank"),
            ).subquery()

            query = (
                session.query(ranked_users_query)
                .filter(ranked_users_query.c.user_id == self.authenticated_user.user_id)
                .with_entities(ranked_users_query.c.rank)
            )
            rank = query.first()

        if rank is None:
            return -1
        return rank[0]

    @rx.var(cache=True, initial_value="")
    def client_config(self) -> str:
        cfg = config.get_config()
        return textwrap.dedent(
            f"""
            export COMPRL_SERVER_URL={cfg.server_url}
            export COMPRL_SERVER_PORT={cfg.port}
            export COMPRL_ACCESS_TOKEN={self.authenticated_user.token}
            """
        ).strip()

    @rx.event
    def update_ranked_users(self) -> None:
        with get_session() as session:
            self.ranked_users = get_ranked_users(session)  # type: ignore

    @rx.var(cache=True, initial_value=())
    def leaderboard_entries(self) -> Sequence[tuple[int, str, float, str]]:
        return [
            (
                i + 1,
                user.username,
                round(user.score(), 2),
                f"{user.mu:.2f} / {user.sigma:.2f}",
            )
            for i, user in enumerate(self.ranked_users)
        ]


class UserGamesState(ProtectedState):
    """State for the user games page."""

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

    @rx.var(cache=True, initial_value=1)
    def page_number(self) -> int:
        return (self.offset // self.limit) + 1 + (1 if self.offset % self.limit else 0)

    @rx.var(cache=True, initial_value=1)
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

    def _get_game_file_path(self, game_id: str) -> pathlib.Path:
        return config.get_config().data_dir / "game_actions" / f"{game_id}.pkl"

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

            game_file_exists = self._get_game_file_path(game.game_id).exists()

            self.user_games.append(
                GameInfo(
                    game.user1_.username,
                    game.user2_.username,
                    result,
                    str(game.start_time.strftime("%Y-%m-%d %H:%M:%S")),
                    str(game.game_id),
                    game_file_exists,
                )
            )

        self.total_items = self._get_num_user_games()

    @rx.event
    def download_game(self, game_id: str):
        game_file_path = self._get_game_file_path(game_id)

        try:
            data = game_file_path.read_bytes()
        except Exception:
            raise RuntimeError("Game file not found") from None

        return rx.download(filename=game_file_path.name, data=data)


class SettingsState(ProtectedState):
    """State for the settings page."""

    username: str = ""
    username_status_message: str = ""
    username_error_message: str = ""

    current_password: str = ""
    new_password: str = ""
    confirm_password: str = ""
    password_status_message: str = ""
    password_error_message: str = ""

    def on_load(self):
        super().on_load()
        self.username = self.authenticated_user.username
        self.username_status_message = ""
        self.username_error_message = ""
        self.password_status_message = ""
        self.password_error_message = ""

    def do_logout(self):
        self.username = ""
        self.username_status_message = ""
        self.username_error_message = ""
        self.current_password = ""
        self.new_password = ""
        self.confirm_password = ""
        self.password_status_message = ""
        self.password_error_message = ""
        return reflex_local_auth.LocalAuthState.do_logout

    def set_username(self, username: str) -> None:
        """Set the username in state."""
        self.username = username

    def set_current_password(self, current_password: str) -> None:
        """Set the current password in state."""
        self.current_password = current_password

    def set_new_password(self, new_password: str) -> None:
        """Set the new password in state."""
        self.new_password = new_password

    def set_confirm_password(self, confirm_password: str) -> None:
        """Set the confirm password in state."""
        self.confirm_password = confirm_password

    def save_username(self, form_data) -> None:
        """Validate and persist a new username."""
        desired_username = form_data["username"].strip()
        self.username = desired_username
        self.username_status_message = ""
        self.username_error_message = ""

        if not desired_username:
            self.username_error_message = "Username cannot be empty."
            return

        if not validate_username(desired_username):
            self.username_error_message = (
                "Username contains invalid characters."
                " Allowed characters: a-Z, 0-9, _, -."
            )
            return

        if desired_username == self.authenticated_user.username:
            self.username_status_message = "Username unchanged."
            return

        with get_session() as session:
            existing_user = session.scalars(
                sa.select(User).where(User.username == desired_username)
            ).one_or_none()

            if existing_user:
                self.username_error_message = "That username is already taken."
                return

            current_user = session.get(User, self.authenticated_user.user_id)
            if current_user is None:
                self.username_error_message = "Could not find current user."
                return

            current_user.username = desired_username
            session.add(current_user)
            session.commit()

        self.username_status_message = "Username updated successfully."

    def save_password(self, form_data):
        """Validate and persist a new password for the current user."""
        current_password = form_data["current_password"]
        new_password = form_data["new_password"]
        confirm_password = form_data["confirm_password"]

        self.password_status_message = ""
        self.password_error_message = ""

        if not current_password or not new_password or not confirm_password:
            self.password_error_message = "All fields are required."
            return

        if len(new_password) < PASSWORD_MIN_LENGTH:
            self.password_error_message = (
                f"Password needs to be at least {PASSWORD_MIN_LENGTH} characters long."
            )
            return

        if new_password != confirm_password:
            self.password_error_message = "Passwords do not match."
            return

        with get_session() as session:
            user = session.get(User, self.authenticated_user.user_id)
            if user is None:
                self.password_error_message = "Could not find current user."
                return

            if not verify_password(user.password, current_password):
                self.password_error_message = "Current password is incorrect."
                return

            user.password = hash_password(new_password)
            session.add(user)
            session.commit()

        self.password_status_message = "Password updated successfully."
        self.current_password = ""
        self.new_password = ""
        self.confirm_password = ""
