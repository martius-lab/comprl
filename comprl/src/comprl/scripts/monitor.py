"""TUI interface for parsing and displaying the contents of a CompRL monitor file."""

from __future__ import annotations

import datetime
import re
import sys
from pprint import pprint
from typing import Any

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DataTable, Label

# Example input
test_data = """2025-01-29 13:24:03.101909

Connected players (3):
        bot-strong [4aba6871-619f-4ff6-b9c5-81c5cb639464]
        bot-weak [be0c0a95-2be3-4cee-beb8-e3eaded5bff3]
        felix-test [770c141b-46aa-4ef0-9982-3fd94fbb32ba]

Games (2):
        4d648d0a-601b-4d11-93df-93593fd97768 ('be0c0a95-2be3-4cee-beb8-e3eaded5bff3', '770c141b-46aa-4ef0-9982-3fd94fbb32ba')
        364fc6fa-0f95-4f1b-922f-c97acc25a9bf ('be0c0a95-2be3-4cee-beb8-e3eaded5bff3', '770c141b-46aa-4ef0-9982-3fd94fbb32ba')

Players in queue (1):
        bot-strong [4aba6871-619f-4ff6-b9c5-81c5cb639464] since 2025-01-28 17:10:42.975318

Match quality scores:
        felix-test vs bot-weak: 121.9780
        felix-test vs bot-strong: 11.3

END
"""  # noqa: E501


# Note: this parser is pretty quick&dirty, so probably not super robust
class Parser:
    """Parser for the CompRL monitor file format."""

    def __init__(self) -> None:
        self.data: dict[str, Any] = {
            "timestamp": None,
            "num_connected_players": None,
            "connected_players": [],
            "num_games": None,
            "games": [],
            "num_players_in_queue": None,
            "players_in_queue": [],
            "match_quality_scores": [],
        }
        # Define the structure of the monitor file as a list of line parser functions.
        # Each function should return True if it parsed a matching line and False if the
        # line did not match.
        # In case a function returns False, the parse will move to the next function and
        # run it on the same line.
        # This is a pretty quick and dirty implementation.  It is not robust to failures
        # somewhere in the middle.
        self.document = [
            self._timestamp,
            self._newline,
            self._header_connected_players,
            self._connected_player,
            self._newline,
            self._header_games,
            self._game,
            self._newline,
            self._header_players_in_queue,
            self._player_in_queue,
            self._newline,
            self._header_match_quality_scores,
            self._match_quality_score,
            self._newline,
            self._end,
        ]

    def parse(self, lines: list[str]) -> None:
        """Parse the lines of the monitor file.

        Args:
            lines: Content of the monitor file split into lines.
        """
        i = 0
        for parser in self.document:
            while i < len(lines):
                if parser(lines[i].rstrip()):
                    i += 1
                else:
                    break

    def _newline(self, line: str) -> bool:
        return line.strip() == ""

    def _timestamp(self, line: str) -> bool:
        try:
            stamp = datetime.datetime.fromisoformat(line)
            self.data["timestamp"] = stamp
        except ValueError:
            return False

        return True

    def _header_connected_players(self, line: str) -> bool:
        m = re.match(r"Connected players \((\d+)\):", line)
        if m:
            self.data["num_connected_players"] = int(m.group(1))
            return True
        return False

    def _connected_player(self, line: str) -> bool:
        m = re.match(r"\s+(\S+) \[(\S+)\]", line)
        if m:
            self.data["connected_players"].append(
                {"player": m.group(1), "uuid": m.group(2)}
            )
            return True
        return False

    def _header_games(self, line: str) -> bool:
        m = re.match(r"Games \((\d+)\):", line)
        if m:
            self.data["num_games"] = int(m.group(1))
            return True
        return False

    def _game(self, line: str) -> bool:
        m = re.match(r"\s+(\S+) \((\S+), (\S+)\)", line)
        if m:
            self.data["games"].append(
                {"game": m.group(1), "player1": m.group(2), "player2": m.group(3)}
            )
            return True
        return False

    def _header_players_in_queue(self, line: str) -> bool:
        m = re.match(r"Players in queue \((\d+)\):", line)
        if m:
            self.data["num_players_in_queue"] = int(m.group(1))
            return True
        return False

    def _player_in_queue(self, line: str) -> bool:
        m = re.match(r"\s+(\S+) \[(\S+)\] since (\S+)", line)
        if m:
            self.data["players_in_queue"].append(
                {"player": m.group(1), "uuid": m.group(2), "timestamp": m.group(3)}
            )
            return True
        return False

    def _header_match_quality_scores(self, line: str) -> bool:
        return line == "Match quality scores:"

    def _match_quality_score(self, line: str) -> bool:
        m = re.match(r"\s+(\S+) vs (\S+): (\S+)", line)
        if m:
            self.data["match_quality_scores"].append(
                {
                    "user1": m.group(1),
                    "user2": m.group(2),
                    "score": float(m.group(3)),
                }
            )
            return True
        return False

    def _end(self, line: str) -> bool:
        if line == "END":
            self.data["end"] = True
            return True
        return False


def test() -> None:
    """Test the parser with the example input."""
    parser = Parser()
    lines = test_data.splitlines()
    parser.parse(lines)

    pprint(parser.data)


class ComprlMonitorApp(App):
    """Textual app for displaying the contents of a CompRL monitor file."""

    CSS = """
        DataTable {
            height: 10;
        }

        .h2 {
            text-style: bold;
            margin: 1;
        }
    """

    def __init__(self, monitor_file_path: str) -> None:
        super().__init__()
        self.monitor_file_path = monitor_file_path

    def compose(self) -> ComposeResult:
        """Compose the TUI layout."""
        yield Header()
        yield Label("Last Update:", id="timestamp", classes="h2")
        yield Label("Connected Players:", classes="h2")
        yield DataTable(id="connected_players")
        yield Label("Running Games:", classes="h2")
        yield DataTable(id="games")
        yield Label("Players in Queue:", classes="h2")
        yield DataTable(id="queue")
        yield Label("Match Quality Scores:", classes="h2")
        yield DataTable(id="match_quality_scores")
        yield Footer()

    def on_mount(self) -> None:
        """Initialise the app."""
        self.title = "CompRL Server Monitor"

        self.reload_data()
        self.update_time = self.set_interval(10, self.reload_data)

    def reload_data(self) -> None:
        """Reload the data from the monitor file and update the content in the TUI."""
        with open(self.monitor_file_path, "r") as f:
            lines = f.readlines()

        parser = Parser()
        parser.parse(lines)

        timestamp: Label = self.query_one("#timestamp")
        timestamp.update(f"Last Update: {parser.data['timestamp']}")

        player_table: DataTable = self.query_one("#connected_players")
        player_table.clear(columns=True)
        player_table.add_columns("User", "Player ID")
        player_table.add_rows(
            [
                (player["player"], player["uuid"])
                for player in parser.data["connected_players"]
            ]
        )

        games_table: DataTable = self.query_one("#games")
        games_table.clear(columns=True)
        games_table.add_columns("Game", "Player 1", "Player 2")
        games_table.add_rows(
            [
                (game["game"], game["player1"], game["player2"])
                for game in parser.data["games"]
            ]
        )

        queue_table: DataTable = self.query_one("#queue")
        queue_table.clear(columns=True)
        queue_table.add_columns("User", "Player ID", "Timestamp")
        queue_table.add_rows(
            [
                (player["player"], player["uuid"], player["timestamp"])
                for player in parser.data["players_in_queue"]
            ]
        )

        match_quality_table: DataTable = self.query_one("#match_quality_scores")
        match_quality_table.clear(columns=True)
        match_quality_table.add_columns("User 1", "User 2", "Score")
        match_quality_table.add_rows(
            sorted(
                [
                    (score["user1"], score["user2"], score["score"])
                    for score in parser.data["match_quality_scores"]
                ],
                key=lambda x: x[2],
                reverse=True,
            )
        )

        self.refresh()


def main() -> None:
    """Run the app."""
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        path = "/dev/shm/comprl_monitor"

    app = ComprlMonitorApp(path)
    app.run()


if __name__ == "__main__":
    main()
