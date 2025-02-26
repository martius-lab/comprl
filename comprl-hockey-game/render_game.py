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
from PIL import Image, ImageDraw, ImageFont
from hockey.hockey_env import HockeyEnv  # type: ignore[import-untyped]


class GameInfo(NamedTuple):
    round: int
    player1: str
    player2: str
    score1: int
    score2: int


def playback_round(
    env: HockeyEnv,
    observations: Sequence[np.ndarray],
    fps: float,
    game_info: GameInfo,
    players_swapped: bool,
    show: bool,
) -> list[np.ndarray]:
    frames = []
    rate_ms = int(1 / fps * 1000)
    env.reset()

    # Show the first frame with annotation of the round for a second
    first_obs = observations[0]
    env.set_state(first_obs)
    img = np.array(
        render(env, game_info, players_swapped, center_text=f"Round {game_info.round}")
    )
    for _ in range(int(fps)):
        frames.append(img)
        if show:
            cv2.imshow("Game", cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
            cv2.waitKey(rate_ms)

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


def playback_final_result(
    env: HockeyEnv,
    final_observation: np.ndarray,
    fps: float,
    game_info: GameInfo,
    players_swapped: bool,
    show: bool,
) -> list[np.ndarray]:
    frames = []
    rate_ms = int(1 / fps * 1000)
    env.reset()

    if game_info.score1 == game_info.score2:
        result = "Draw"
    elif game_info.score1 > game_info.score2:
        result = f"{game_info.player1} wins"
    else:
        result = f"{game_info.player2} wins"

    env.set_state(final_observation)
    img = np.array(render(env, game_info, players_swapped, center_text=result))
    for _ in range(int(fps * 2)):
        frames.append(img)
        if show:
            cv2.imshow("Game", cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
            cv2.waitKey(rate_ms)

    return frames


def render(
    env: HockeyEnv,
    game_info: GameInfo,
    players_swapped: bool,
    center_text: str | None = None,
) -> Image.Image:
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

    if center_text:
        font = ImageFont.truetype(font_file, 50)
        draw.text(
            (img.width / 2, img.height / 2),
            center_text,
            (19, 19, 19),
            font=font,
            anchor="mm",
        )

    return img


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("game_file", type=pathlib.Path, help="Game file.")
    parser.add_argument("--fps", type=float, default=35.0, help="Playback framerate.")
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

    env = HockeyEnv()

    frames = []
    game_info = GameInfo(1, data["user_names"][0], data["user_names"][1], 0, 0)
    for i, round_ in enumerate(data["rounds"]):
        players_swapped = args.swap_players and bool(i % 2)
        frames += playback_round(
            env,
            round_["observations"],
            args.fps,
            game_info,
            players_swapped,
            show=not args.save_video,
        )
        time.sleep(1)

        # update game info for next round
        game_info = GameInfo(
            i + 2,
            data["user_names"][0],
            data["user_names"][1],
            int(round_["score"][0]),
            int(round_["score"][1]),
        )

    # show last frame with the final score
    frames += playback_final_result(
        env,
        round_["observations"][-1],
        args.fps,
        game_info,
        players_swapped,
        show=not args.save_video,
    )

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
