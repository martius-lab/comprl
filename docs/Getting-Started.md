**This documentation refers to version 0.1.0.  For later versions, some things may be different.**

# Server

To host your competition, implement a new game by inheriting from the `IGame` interface provided by the `comprl.server.interfaces` module (for more see [here](#implementing-the-igame-interface)). Once your game is fully implemented, use a configuration file or command-line arguments to start the server with the desired configuration (for more see [here](#config-file)).

```sh
#display all possible command line arguments
python -m comprl.server --h

#run the server by providing a config file
python -m comprl.server --config="path/to/config.toml"
```

## Implementing the `IGame` Interface

The Game Class only implements game logic and does not have to handle networking (e.g. collecting actions, disconnected players), matchmaking or database tasks. In general, a Game can also implement a game with more than two players, but the Matchmaking and the Database has to be updated for this.

Start implementing the interface with
```python
from comprl.server.interfaces import IGame, IPlayer

class MyGame(IGame):
    def __init__(self, players: list[IPlayer]) -> None:
        super().__init__(players)

    ...
```
and implement all the necessary methods listed below:

- `update(actions: dict[PlayerID, list[float]]) -> bool`

  * Updates the environment 
  * Input: All the collected actions in a dictionary
  * Returns `True` if the game should end `False` otherwise

- `_validate_action(action: list[float])`

  * Returns `True` if the action is valid
  * Disconnects the player if the action is invalid which ends the game

- `_get_observation(id: PlayerID) -> list[float]`
  * Returns the observation that should be sent to this player
  * Observations can be sent to each player individually (e.g. for left and right players)

- `_player_won(id: PlayerID) -> bool`

  * Returns `True` if the player has won, `False` otherwise
  * Should return `False` for all players in case of a draw

- `_player_stats(id: PlayerID) -> list[float]`

  * Is called at the end of the game
  * Can be used to communicate Statistics at the end of the game
  * e.g. scores, disconnects, rounds, ...

For the implementation of these methods the following instance variables can be helpful:

- `self.players: dict[PlayerID, Player]` a dictionary with all players of the game

- `self.scores: dict[PlayerID, float]` a dictionary with all scores (defaults to all scores 0.0)

## Config File

To start the server with the game, use a toml config file to set several parameters of the server. When specifying a config file all parameters can also be overwritten by the fitting command line argument. The supported arguments in a config file are:
- `--config` path to the config file
- `--port` Port to listen on
- `--timeout` Seconds to wait for a player to answer
- `--game_path` File containing the game logic to run
- `--game_class` Classname of the game
- `--log` Log level
- `--game_db_path` Path to the database file (doesn't have to exist)
- `--game_db_name` Name of the game table in the file
- `--user_db_path` Path to the database file
- `--user_db_name` Name of the user table in the file
- `--match_quality_threshold` Threshold for matching players
- `--percentage_min_players_waiting` Percentage of players always waiting in queue
- `--percental_time_bonus` (Minutes waiting * percentage) added as a time bonus for waiting players

For examples of a config file see [here](#examples).
    
## Stored game actions

The actions of each game are stored in a python dictionary and this dictionary is stored in a file using the [pickle library](https://docs.python.org/3/library/pickle.html). The actions can be retrieved with the key `""actions""`.

Additionally, the files of hockey games support the following keys:
- `num_rounds`: number of rounds played
- `actions_round_0`: actions of the first round
- `actions_round_1`: actions of the second round
- ...
- `actions_round_(num_rounds-1)`: actions of the last round
- `observations_round_0`: observations of the first round
- ...

## Scripts

The following three scripts can be helpful to handle the user database.
```sh
#script to add dummy user to the user database
python -m comprl.scripts.dummy_user

#script to add new user to the user database
python -m comprl.scripts.new_user

#script to reset the game database and the mu and sigma in the user database
python -m comprl.scripts.reset
```
The database information can be given by line parameter or by the same config file that is used for the server. For example:
```
python -m comprl.scripts.dummy_user --config="examples/hockey/config.toml"
```


# Client

For implementing a new client, utilize the `comprl.client` package. Here, you can directly instantiate an `Agent` object or inherit from it. The only required implementation is the `get_step()` function, which is called with the corresponding action. Additionally, override other functions to receive and handle data about games being played or handle any errors that may occur. The flexibility provided by COMPRL allows you to tailor the client to your specific needs.

The `Agent` class also supports decorators for an easy implementation of the needed functions. 

```python
from comprl.client import Agent

myAgent = Agent()

@myAgent.event
def get_step(obv: list[float]):
    ...
```
A simple example can be found in [`examples/simple/agent.py`](https://github.com/martius-lab/teamproject-competition-server/blob/main/examples/simple/agent.py).

#### Methods of the `Agent` interface
- `get_step(obv: list[float]) -> list[float]`

  * has to be implemented
  * gets an observation as input
  * returns the next action
  * How to interpret the observation and the action has to be specified separately

- `on_start_game(game_id: UUID)`

  * is called, when the game starts
  * Game-ID (UUID) can be stored to find games later

- `on_end_game(result: bool, stats: list[float])`

  * is called, when the game ends
  * Result indicates, if the game was won
  * Stats are all statistics that the player should receive (e.g. scores)

- `is_ready() -> bool`

  * Is called, to ask if the client is ready for an other game
  * Can be used to disconnect smoothly (e.g. after 10 games)
  * Retuns true by default

- `on_error(msg)`, `on_message(msg)`, `on_disconnect()`

  * Are used for communication from the server to the client
  * Print a message by default

# Web

* Based on React using Remix and Material UI
* Users can register by a provided Master-Key.
* Authentication is implemented by using the Remix-Auth package.
* Multi-Page-Dashboard
* Responsive Design

## Development

From your terminal:

```sh
npm run dev
```

This starts your app in development mode, rebuilding assets on file changes.

## Deployment

First, build your app for production:

```sh
npm run build
```

Then run the app in production mode:

```sh
npm start
```

Now you'll need to pick a host to deploy it to.

## Config File
The `user_db_path`, the `user_db_name` and the `key` are defined in the config file `config.toml`.
The current key is `1234`.

# Examples

## Simple
This example can be found in [`\examples\simple`](https://github.com/martius-lab/teamproject-competition-server/tree/main/examples/simple).

The game logic is very simple: The two agents send integers, these are added up, when the sum reaches 10 the game ends. The sent integers can be manually entered in the console. This game is supposed to demonstrates the basics of a game and can be used for easy testing.
```sh
#run game by providing a config file
python -m comprl.server --config="examples/simple/config.toml"

#run agent
python -m examples.simple.agent
```

## Rock-Paper-Scissors

This example can be found in [`examples/rockpaperscissors`](https://github.com/martius-lab/teamproject-competition-server/tree/main/examples/rockpaperscissors).

In this game the two agents play rock-paper-scissors until one of them has won three times. The agent sent random actions.

```sh
#run game by providing a config file
python -m comprl.server --config="examples/rockpaperscissors/config.toml"

#run agent
python -m examples.rockpaperscissors.agent
```

## Hockey

This example can be found in [`examples/hockey`](https://github.com/martius-lab/teamproject-competition-server/tree/main/examples/hockey).

Two agents play several rounds of the [hockey game](https://github.com/martius-lab/laser-hockey-env/). After each round sides are swapped.
```sh
#run game by providing a config file
python -m comprl.server --config="examples/hockey/config.toml"

#run one of the following agents
python -m examples.hockey.weak_hockey_agent
python -m examples.hockey.strong_hockey_agent
python -m examples.hockey.random_hockey_agent
```