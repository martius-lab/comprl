"""Manager users in the database."""

from __future__ import annotations

import logging
import pprint
import sys
import uuid
from typing import Annotated

import sqlalchemy as sa
import tabulate
import typer

from comprl.server.data.sql_backend import Game, User, hash_password
from comprl.server.data.interfaces import UserRole
from comprl.server.data import UserData


app = typer.Typer()


@app.command()
def list(
    database: Annotated[str, typer.Argument(help="Path to the database file.")],
    ranked: Annotated[
        bool, typer.Option("--ranked", help="Order user based on ranking.")
    ],
) -> None:
    """List all users."""
    engine = sa.create_engine(f"sqlite:///{database}")

    data = []
    with sa.orm.Session(engine) as session:
        if ranked:
            stmt = sa.select(User).order_by((User.mu - User.sigma).desc())
        else:
            stmt = sa.select(User)
        users = session.scalars(stmt).all()

        for user in users:
            num_games_played = (
                session.query(Game)
                .filter(
                    sa.or_(
                        Game.user1 == user.user_id,
                        Game.user2 == user.user_id,
                    )
                )
                .with_entities(sa.func.count())
                .scalar()
            )

            num_games_won = (
                session.query(Game)
                .filter(Game.winner == user.user_id)
                .with_entities(sa.func.count())
                .scalar()
            )

            num_disconnects = (
                session.query(Game)
                .filter(Game.disconnected == user.user_id)
                .with_entities(sa.func.count())
                .scalar()
            )

            data.append(
                (
                    user.user_id,
                    user.username,
                    user.role,
                    user.mu,
                    user.sigma,
                    num_games_played,
                    num_games_won,
                    num_disconnects,
                )
            )

    print(
        tabulate.tabulate(
            data,
            headers=[
                "ID",
                "Username",
                "Role",
                "Mu",
                "Sigma",
                "Games Played",
                "Games Won",
                "Disconnects",
            ],
        )
    )


@app.command()
def show(
    database: Annotated[str, typer.Argument(help="Path to the database file.")],
    username: Annotated[str, typer.Argument(help="Name of the user")],
) -> None:
    """Show user entry."""
    engine = sa.create_engine(f"sqlite:///{database}")
    with sa.orm.Session(engine) as session:
        user = session.scalar(sa.select(User).where(User.username == username))

    if user is None:
        logging.error("User '%s' does not exist", username)
        raise typer.Exit(1)

    # print the user entry
    pprint.pprint(user)


@app.command()
def add(
    database: Annotated[str, typer.Argument(help="Path to the database file.")],
    username: Annotated[str, typer.Argument(help="Name of the user")],
    password: Annotated[
        str,
        typer.Option(
            "--password",
            prompt=True,
            confirmation_prompt=True,
            hide_input=True,
            help="Password",
        ),
    ],
    role: Annotated[
        UserRole, typer.Option("--role", help="Set user role (default: USER)")
    ] = UserRole.USER,
) -> None:
    """Create a new user."""
    user_data = UserData(database)

    token = str(uuid.uuid4())
    user_data.add(
        user_name=username, user_password=password, user_token=token, user_role=role
    )


@app.command()
def edit(
    database: Annotated[str, typer.Argument(help="Path to the database file.")],
    username: Annotated[str, typer.Argument(help="Name of the user")],
    set_password: Annotated[
        bool,
        typer.Option(
            "--set-password",
            help="Set new password",
        ),
    ] = False,
    role: Annotated[
        UserRole | None, typer.Option("--set-role", help="Set new role")
    ] = None,
) -> None:
    """Edit a user entry."""
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] [%(name)s | %(levelname)s] %(message)s",
    )

    engine = sa.create_engine(f"sqlite:///{database}")

    with sa.orm.Session(engine) as session:
        changed = False
        user = session.scalar(sa.select(User).where(User.username == username))

        if user is None:
            print("User '%s' does not exist" % username, file=sys.stderr)
            raise typer.Exit(1)

        if set_password:
            new_pw = typer.prompt(
                f"New password for user {username}:",
                hide_input=True,
                confirmation_prompt=True,
            )
            user.password = hash_password(new_pw)
            changed = True

        if role:
            user.role = role.value
            changed = True

        if changed:
            session.commit()
            session.refresh(user)

    # print the user entry
    pprint.pprint(user)


if __name__ == "__main__":
    app()
