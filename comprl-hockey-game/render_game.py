#!/usr/bin/env python3
"""Play back a comprl hockey game based on the recorded actions."""

from __future__ import annotations

import argparse
import contextlib
import logging
import pathlib
import pickle
import sys
import time
from typing import NamedTuple, Sequence

import cv2
import imageio
import numpy as np
import sqlalchemy as sa
from PIL import Image, ImageDraw, ImageFont
from hockey.hockey_env import HockeyEnv  # type: ignore[import-untyped]

from comprl.server.data.sql_backend import Game


class GameInfo(NamedTuple):
    player1: str
    player2: str
    score1: int | None
    score2: int | None


def playback(
    env: HockeyEnv,
    observations: Sequence[np.ndarray],
    rate_ms: int,
    game_info: GameInfo,
    players_swapped: bool,
    show: bool,
) -> list[np.ndarray]:
    frames = []
    env.reset()
    t_start = time.monotonic()
    for observation in observations:
        env.set_state(observation)
        img = np.array(render(env, game_info, players_swapped))
        frames.append(img)
        if show:
            cv2.imshow("Game", cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
            duration = max(1, int(rate_ms - (time.monotonic() - t_start) * 1000))
            cv2.waitKey(duration)

    return frames


def render(env: HockeyEnv, game_info: GameInfo, players_swapped: bool) -> Image.Image:
    red = (235, 98, 53)
    blue = (93, 158, 199)

    frame = env.render(mode="rgb_array")
    img = Image.fromarray(frame)
    draw = ImageDraw.Draw(img)

    font_file = pathlib.Path(__file__).parent / "f2-tecnocratica-ffp.ttf"
    font = ImageFont.truetype(font_file, 24)

    if players_swapped:
        player_left = game_info.player2
        player_right = game_info.player1
        score_left = game_info.score2
        score_right = game_info.score1
    else:
        player_left = game_info.player1
        player_right = game_info.player2
        score_left = game_info.score1
        score_right = game_info.score2

    text_offset = 15
    draw.rectangle((0, 0, img.width, 28), fill=(100, 100, 100))
    draw.text((text_offset, 0), player_left[:25], red, font=font)
    draw.text(
        (img.width - text_offset, 0),
        player_right[:25],
        blue,
        font=font,
        align="right",
        anchor="ra",
    )

    if game_info.score1 is not None and game_info.score2 is not None:
        score_center_offset = 5
        draw.text((img.width / 2, 0), ":", (200, 200, 200), font=font, anchor="ma")
        draw.text(
            (img.width / 2 - score_center_offset, 0),
            str(score_left),
            red,
            font=font,
            anchor="ra",
        )
        draw.text(
            (img.width / 2 + score_center_offset, 0),
            str(score_right),
            blue,
            font=font,
            anchor="la",
        )

    return img


def get_game_info(database: pathlib.Path, game_id: int) -> GameInfo:
    engine = sa.create_engine(f"sqlite:///{database}")
    with sa.orm.Session(engine) as session:
        stmt = sa.select(Game).where(Game.game_id == game_id)
        game = session.scalar(stmt)

        assert game is not None, f"Game {game_id} not found in database."
        return GameInfo(
            player1=game.user1_.username,
            player2=game.user2_.username,
            score1=int(game.score1),
            score2=int(game.score2),
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("game_file", type=pathlib.Path, help="Game file.")
    parser.add_argument("--fps", type=float, default=35.0, help="Playback framerate.")
    parser.add_argument(
        "--database", type=pathlib.Path, help="Database to look up game info."
    )
    parser.add_argument(
        "--save-video",
        type=pathlib.Path,
        metavar="dest",
        help="Save as MP4 video to the specified path.",
    )
    parser.add_argument(
        "--swap-players",
        action="store_true",
        help="""Swap players after each round.  This is only needed for old game files.
        The current game implementation does not swap players anymore.
        This flag only affects the display of player names and scores.
        """,
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output."
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="[%(asctime)s] [%(name)s | %(levelname)s] %(message)s",
    )

    if args.save_video and args.save_video.exists():
        print(f"{args.save_video} already exists. Exiting.")
        return 1

    with open(args.game_file, "rb") as f:
        data = pickle.load(f)

    num_rounds = data["num_rounds"][0][0]

    if args.database:
        game_id = args.game_file.stem
        game_info = get_game_info(args.database, game_id)
    else:
        game_info = GameInfo("Player 1", "Player 2", None, None)

    env = HockeyEnv()

    rate_ms = int(1 / args.fps * 1000)
    frames = []
    for i in range(num_rounds):
        players_swapped = args.swap_players and bool(i % 2)
        frames += playback(
            env,
            data[f"observations_round_{i}"],
            rate_ms,
            game_info,
            players_swapped,
            show=not args.save_video,
        )
        time.sleep(1)

    if args.save_video:
        video = imageio.get_writer(
            args.save_video,
            fps=args.fps,
            codec="mjpeg",
            quality=10,
            pixelformat="yuvj444p",
        )
        for frame in frames:
            video.append_data(frame)
        video.close()

    return 0


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        sys.exit(main())
